import webrtcvad
import collections
import sys
from datetime import datetime

class Frame():
    """Represents a "frame" of audio data."""
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration

class AWSTranscribeVad():
    def __init__(self, sampleRate, frame_duration_ms, padding_duration_ms, caller=None):
        super().__init__()
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(3)
        self.sampleRate = sampleRate
        self.frame_duration_ms = frame_duration_ms
        self.padding_duration_ms = padding_duration_ms
        self.voiced_frames = []
        self.leftVadBuffer = bytearray()
        self.num_padding_frames = int(self.padding_duration_ms / self.frame_duration_ms)
        self.ring_buffer = collections.deque(maxlen=self.num_padding_frames)
        self.triggered = False
        self.completedVad = False
        self.caller = caller
        self.on_vad_changed = None

    def asyncCallback(self, on_vad_changed):
        # on_vad_changed: callable object which is called when vad state is changed.
        # on_message has 2 arguments.
        # The first argument is self object
        # The second argument is trigger state.
        # The third argument is support for completing state
        self.on_vad_changed = on_vad_changed
    
    def frameGenerator(self, audio):
        """Generates audio frames from PCM audio data.
        Takes the desired frame duration in milliseconds, the PCM data, and
        the sample rate.
        Yields Frames of the requested duration.
        """
        
        if len(self.leftVadBuffer) > 0:
            audio = audio + self.leftVadBuffer
        n = int(self.sampleRate * (self.frame_duration_ms / 1000.0) * 2)
        offset = 0
        timestamp = 0.0
        duration = (float(n) / self.sampleRate) / 2.0
        frames = []
        while offset + n < len(audio):
            frame = Frame(audio[offset:offset + n], timestamp, duration)
            frames.append(frame)
            timestamp += duration
            offset += n

        remainLen =len(audio) - offset
        self.leftVadBuffer = audio[len(audio) - remainLen: len(audio)]
        return frames

    def vad_collector(self, audio, frames):
        """Filters out non-voiced audio frames.
        Given a webrtcvad.Vad and a source of audio frames, yields only
        the voiced audio.
        Uses a padded, sliding window algorithm over the audio frames.
        When more than 90% of the frames in the window are voiced (as
        reported by the VAD), the collector triggers and begins yielding
        audio frames. Then the collector waits until 90% of the frames in
        the window are unvoiced to detrigger.
        The window is padded at the front and back to provide a small
        amount of silence or the beginnings/endings of speech around the
        voiced frames.
        Arguments:
        sample_rate - The audio sample rate, in Hz.
        frame_duration_ms - The frame duration in milliseconds.
        padding_duration_ms - The amount to pad the window, in milliseconds.
        vad - An instance of webrtcvad.Vad.
        frames - a source of audio frames (sequence or generator).
        Returns: A generator that yields PCM audio data.
        """
        # We have two states: TRIGGERED and NOTTRIGGERED. We start in the
        # NOTTRIGGERED state.
        for frame in frames:
            is_speech = self.vad.is_speech(frame.bytes, self.sampleRate)
            if not self.triggered:
                self.ring_buffer.append((frame, is_speech))
                self.num_voiced = len([f for f, speech in self.ring_buffer if speech])
                # If we're NOTTRIGGERED and more than 90% of the frames in
                # the ring buffer are voiced frames, then enter the
                # TRIGGERED state.
                if self.num_voiced > 0.9 * self.ring_buffer.maxlen:
                    self.triggered = True
                    # We want to yield all the audio we see from now until
                    # we are NOTTRIGGERED, but we have to start with the
                    # audio that's already in the ring buffer.
                    for f, s in self.ring_buffer:
                        self.voiced_frames.append(f)
                    self.ring_buffer.clear()
            else:
                # We're in the TRIGGERED state, so collect the audio data
                # and add it to the ring buffer.
                self.voiced_frames.append(frame)
                self.ring_buffer.append((frame, is_speech))
                self.num_unvoiced = len([f for f, speech in self.ring_buffer if not speech])
                # If more than 90% of the frames in the ring buffer are
                # unvoiced, then enter NOTTRIGGERED and yield whatever
                # audio we've collected.
                if self.num_unvoiced > 0.9 * self.ring_buffer.maxlen:
                    print('vad finished %s' % datetime.now())
                    self.triggered = False
                    self.completedVad = True
                    if self.on_vad_changed:
                        self.on_vad_changed(self, self.triggered, self.completedVad)
                    voicedBytes = b''
                    for frame in self.voiced_frames:
                        voicedBytes = voicedBytes + frame.bytes
                    self.ring_buffer.clear()
                    self.voiced_frames = []

        if self.triggered:
            if self.on_vad_changed:
                self.on_vad_changed(self, self.triggered, self.completedVad)
            # print('-(%s)' % (frame.timestamp + frame.duration))
            # print("vad date: %s" % datetime.now())
        # If we have any leftover voiced audio when we run out of input,
        # yield it.
        leftVoice = b'' 
        if self.voiced_frames:
            for frame in self.voiced_frames:
                leftVoice = leftVoice + frame.bytes
        return leftVoice