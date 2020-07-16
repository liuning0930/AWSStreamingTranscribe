from AWSTranscribeStreamingTranscriptResultStream import AWSTranscribeStreamingTranscriptResultStream

class AWSTranscribeEventStreamDecoder():
    def __init__(self):
        super().__init__()

    def decodeEvent(self, data):
        if not self.verifyPreludeForData(data):
            return None

        if not self.verifyMessageLengthHeaderForData(data):
            return None

        headers = self.getHeadersForData(data)
        print('Response headers: %s' % headers)

        body = self.getBodyForData(data)
        print('First 100 bytes of body: %s' % body[0:100])
        resultStream = AWSTranscribeStreamingTranscriptResultStream()
        resultStream = resultStream.resultStreamForWSSBody(body, headers)
        return resultStream
        
    def getHeadersForData(self, data):
        headerLen = self.getHeaderLengthForData(data)
        headerData = data[12: 12+headerLen]
        currentPosition = 0
        dictionary = {}

        while currentPosition < headerLen:
            currentHeaderLen = int.from_bytes(headerData[ currentPosition: currentPosition + 1], "big") 
            currentPosition = currentPosition + 1
            headerKeyBytes = headerData[currentPosition: currentPosition +  currentHeaderLen]
            headerKey = headerKeyBytes.decode('utf-8')
            print('Header Name: %s' % headerKey)
            currentPosition = currentPosition + currentHeaderLen

            # skip header type info, always 7 while decoding
            currentPosition = currentPosition + 1
            currentHeaderValueBytes = headerData[currentPosition: currentPosition + 2]
            currentHeaderValueLen = int.from_bytes(currentHeaderValueBytes, 'big')
            currentPosition = currentPosition + 2
        
            headerValueBytes = headerData[currentPosition: currentPosition + currentHeaderValueLen]
            headerValue = headerValueBytes.decode('utf-8')
            print('Header Value: %s' % headerValue)
            dictionary[headerKey] = headerValue
            currentPosition = currentPosition + currentHeaderValueLen

        return dictionary

    def getBodyForData(self, data):
        headerLen = self.getHeaderLengthForData(data)
        messageLen = len(data)
        dataStartPos = 4+ 4 +4 + headerLen
        dataLen = messageLen - dataStartPos - 4
        bodyBytes = data[dataStartPos: dataStartPos+dataLen]
        dataString = bodyBytes.decode("utf-8") 
        return dataString

    def verifyPreludeForData(self, data):
        if len(data) < 16:
            return False
        return True

    def verifyMessageLengthHeaderForData(self, data):
        totalLength = self.getTotalLengthForData(data)
        return len(data) >= totalLength

    def getTotalLengthForData(self, data):
        totalLengthBytes = data[0:4]
        totalLength = int.from_bytes(totalLengthBytes, "big")  
        return totalLength

    def getHeaderLengthForData(self, data):
        headerLengthBytes = data[4:8]
        headerLength = int.from_bytes(headerLengthBytes, "big") 
        return headerLength

