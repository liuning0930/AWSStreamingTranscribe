import websocket
import time
import sys
import os
import base64
import datetime
import hashlib
import hmac
import urllib
import _thread as thread
import pyaudio

from datetime import datetime
from six.moves import queue

from AWSTranscribeEventStreamenCoding import AWSTranscribeEventStreamenCoding
from AWSTranscribeEventStreamDecoder import AWSTranscribeEventStreamDecoder
from AWSTranscribeVad import AWSTranscribeVad
from AWSTranscribeVad import Frame

ACCESS_KEY = ""
SECRET_KEY = ""

AWS_REGION = "us-east-1"
END_POINT = "wss://transcribestreaming.%s.amazonaws.com:8443" % AWS_REGION

# Audio recording parameters
STREAMING_LIMIT = 240000  # 4 minutes
SAMPLE_RATE = 16000
CHUNK_SIZE = 4096
# CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100m

def on_message(ws, message):
    # print("[Websocket] message: %s" % message)
    if isinstance(message, (bytes, bytearray)):
        print('start decoder ======= ')
        decoder = AWSTranscribeEventStreamDecoder()
        resultStream = decoder.decodeEvent(message)
        print('stop decoder =======')
        for result in resultStream.transcriptEvent.results:
            print(result.alternatives)
        
def on_cont_message(ws, message, flag):
    print("[Websocket] on_cont_message: %s" % message)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_data(ws, message, datatype, flag):
    print("Message: %s type: %s flag: %s" % (message, datatype, flag))

# Indicate that socket built successfully
def on_open(ws):
    def send(*args):
        print(ws.caller.closed)
        while not ws.caller.closed:
            chunk = ws.caller._buff.get()
            frames = ws.caller.audioVad.frameGenerator(chunk)
            ws.caller.audioVad.vad_collector(chunk, frames)
            if chunk and not ws.caller.closed:
                event = AWSTranscribeEventStreamenCoding()
                headers = {
                    ":content-type": "application/octet-stream",
                    ":message-type": "event",
                    ":event-type": "AudioEvent"
                }
                event.construct(chunk, len(chunk), headers)
                ws.send(event.eventBytes, websocket.ABNF.OPCODE_BINARY)
    thread.start_new_thread(send, ())

# vad callback ----------------------------------------------------
def on_vad_changed(vad, triggered, completed):
    print('on_vad_changed: triggered: %s compeleted: %s' % (triggered, completed))
    if (completed):
        caller = vad.caller
        caller.closed = True
        caller.endTranscribe()

class LPWebSocket(websocket.WebSocketApp):
     def __init__(self, url, caller, header=None,
                 on_open=None, on_message=None, on_error=None,
                 on_close=None, on_ping=None, on_pong=None,
                 on_cont_message=None,
                 keep_running=True, get_mask_key=None, cookie=None,
                 subprotocols=None,
                 on_data=None):
        super().__init__(url, header, on_open, on_message, 
                on_error, on_close, on_ping, on_pong, on_cont_message,
                keep_running, get_mask_key, cookie, subprotocols, on_data)
        self.caller = caller

class TranscribeWebSocket():
    def __init__(self, rate, chunk_size):
        super().__init__()
        self._buff = queue.Queue()
        self._rate = rate
        self.chunk_size = chunk_size
        self._num_channels = 1
        self._audio_interface = pyaudio.PyAudio()
        self.audioVad = AWSTranscribeVad(SAMPLE_RATE, 20, 1600, self)
        self.audioVad.asyncCallback(on_vad_changed=on_vad_changed)

    def _fill_buffer(self, in_data, *args, **kwargs):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        frames = self.audioVad.frameGenerator(in_data)
        self.audioVad.vad_collector(in_data, frames)
        return None, pyaudio.paContinue

    def run(self):
        print('start date: %s' % datetime.now())
        self.closed = False
        self.startRecord()
        self.startConnection()

    def startRecord(self):
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=self._num_channels,
            rate=self._rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

    def endTranscribe(self):
        headers = {
                ":message-type": "event",
                ":event-type": "AudioEvent"
            }
        chunk = bytearray()
        event = AWSTranscribeEventStreamenCoding()
        event.construct(chunk, len(chunk), headers)
        if self.ws.sock:
            try:
                self.ws.send(event.eventBytes, websocket.ABNF.OPCODE_BINARY)
                self._audio_stream.stop_stream()
                self._audio_stream.close()
            except Exception as identifier:
                self._audio_stream.stop_stream()
                self._audio_stream.close()
                print("*** Exception " + identifier)
        

    def startConnection(self):
        # HTTP verb
        method = "GET"
        # Service name
        service = "transcribe"
        # AWS Region
        region = AWS_REGION
        # Amazon Transcribe streaming endpoint
        endpoint = END_POINT
        # Host
        host = "transcribestreaming.%s.amazonaws.com:8443" % AWS_REGION

        # Create a date for headers and the credential string
        t = datetime.utcnow()
        amzdate = t.strftime('%Y%m%dT%H%M%SZ')
        datestamp = t.strftime('%Y%m%d') # Date w/o time, used in credential scope

        canonical_uri = "/stream-transcription-websocket"
        canonical_headers = "host:" + host + "\n"
        signed_headers = "host"        
        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = datestamp + "/" + region + "/" + service + "/" + "aws4_request"

        canonical_querystring  = "X-Amz-Algorithm=" + algorithm
        canonical_querystring += "&X-Amz-Credential=" + urllib.parse.quote_plus(ACCESS_KEY + '/' + credential_scope)
        # canonical_querystring += "&X-Amz-Credential="+ SECRET_KEY + "/" + credential_scope
        canonical_querystring += "&X-Amz-Date=" + amzdate 
        canonical_querystring += "&X-Amz-Expires=300"
        # canonical_querystring += "&X-Amz-Security-Token=" + SECRET_KEY
        canonical_querystring += "&X-Amz-SignedHeaders=" + signed_headers
        canonical_querystring += "&language-code=en-US&media-encoding=pcm&sample-rate=16000"
        payload_hash = hashlib.sha256(('').encode('utf-8')).hexdigest()

        canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

        string_to_sign= algorithm + "\n" + amzdate + "\n" + credential_scope + "\n" + hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()

        #Create the signing key
        signing_key = self.getSignatureKey(SECRET_KEY, datestamp, region, service)
                
        # Sign the string_to_sign using the signing key
        signature = hmac.new(signing_key, (string_to_sign).encode("utf-8"), hashlib.sha256).hexdigest()

        canonical_querystring += "&X-Amz-Signature=" + signature
        request_url = endpoint + canonical_uri + "?" + canonical_querystring

        self.ws = LPWebSocket(request_url, 
                              self,
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close,
                              on_data = on_data)
        self.ws.on_open = on_open
        self.on_cont_message = on_cont_message
        self.ws.run_forever()

    def sign(self, key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def getSignatureKey(self, key, dateStamp, regionName, serviceName):
        kDate = self.sign(("AWS4" + key).encode("utf-8"), dateStamp)
        kRegion = self.sign(kDate, regionName)
        kService = self.sign(kRegion, serviceName)
        kSigning = self.sign(kService, "aws4_request")
        return kSigning

if __name__ == "__main__":
    tws = TranscribeWebSocket(SAMPLE_RATE, CHUNK_SIZE)
    tws.run()
     
