import zlib

HEADERS_LENGTH = 16
PRELUDE_LENGTH = 8
PRELUDE_CRC_LENGTH = 4
MESSAGE_CRC_LENGTH = 4

# HEADERS
HEADER_NAME_BYTE_LENGTH = 1
HEADER_NAME = ":content-type"
HEADER_NAME_LENGTH = 13
HEADER_VALUE_TYPE = 7
HEADER_VALUE_STRING = "application/octet-stream"
HEADER_VALUE_BYTE_LENGTH = 24

#PRELUDE
PRELUDE_TOTAL_BYTE_LENGTH = 4
PRELUDE_HEADERS_BYTE_LENGTH = 4
PRELUDE_CRC_LENGTH = 4

#MESSAGE
MESSAGE_CRC_LENGTH = 4

class AWSTranscribeEventStreamenCoding():
    def __init__(self):
        super().__init__()
        self.headerBytes = None
        self.eventBytes = None

    def construct(self, raw, rawLength, headers):
        print('RAW length: %d' % rawLength)
        self.eventBytes =  self.encodeChunk(raw, headers)

        # totalLength = 0
        # headerLength = self.constructHeader()
        # # 1. add prelude length and headers length
        # totalLength = totalLength + headerLength + PRELUDE_TOTAL_BYTE_LENGTH + PRELUDE_HEADERS_BYTE_LENGTH + PRELUDE_CRC_LENGTH
        # # 2. add payload length and message crc length
        # totalLength = totalLength + rawLength + MESSAGE_CRC_LENGTH

        # # The total byte-length.
        # resultBytes = (totalLength).to_bytes(4, byteorder='big')
        # self.eventBytes = bytearray(resultBytes)
        
        # # The headers byte-length. 
        # resultBytes = (headerLength).to_bytes(4, byteorder='big')
        # self.eventBytes = self.eventBytes + bytearray(resultBytes)

        # # The 4-byte CRC checksum for the prelude portion of the message, excluding the CRC itself.
        # preludeCRCInt = self.produceCRC32(self.eventBytes) 
        # resultBytes = (preludeCRCInt).to_bytes(4, byteorder='big')
        # self.eventBytes = self.eventBytes + bytearray(resultBytes)

        # self.eventBytes = self.eventBytes + bytearray(self.headerBytes)
        # self.eventBytes = self.eventBytes + bytearray(raw)

        # messageCRCInt = self.produceCRC32(self.eventBytes)
        # resultBytes = messageCRCInt.to_bytes(4, byteorder='big')
        # self.eventBytes = self.eventBytes + bytearray(resultBytes)

        # return self.eventBytes


    def produceCRC32(self, data):
        t = zlib.crc32(data) 
        return t

    def constructHeader(self):
        # Header name byte-length: The byte-length of the header name.
        headerLength = 0
        resultBytes = (HEADER_NAME_LENGTH).to_bytes(1, byteorder='big')
        headerLength = headerLength + 1
        self.headerBytes = bytearray(resultBytes)

        # Header name: The name of the header indicating the header type.
        # For valid values, see the following frame descriptions.
        resultBytes = HEADER_NAME.encode()
        headerLength = headerLength + HEADER_NAME_LENGTH
        self.headerBytes= self.headerBytes + bytearray(resultBytes)
        # Header value type: An enumeration indicating the header value type.
        resultBytes = (HEADER_VALUE_TYPE).to_bytes(1, byteorder='big')
        headerLength = headerLength + 1
        self.headerBytes = self.headerBytes + bytearray(resultBytes)

        # Value string byte length: The byte-length of the header value string.
        resultBytes = (HEADER_VALUE_BYTE_LENGTH).to_bytes(2, byteorder='big')
        headerLength = headerLength + 2
        self.headerBytes = self.headerBytes + bytearray(resultBytes)

        # Header value: The value of the header string.
        # Valid values for this field depend on the type of header.
        # For valid values, see the following frame descriptions.
        resultBytes = HEADER_VALUE_STRING.encode()
        headerLength = headerLength + HEADER_VALUE_BYTE_LENGTH
        self.headerBytes = self.headerBytes + bytearray(resultBytes)
        return headerLength
    
    def encodeChunk(self, data, headers):
        headersLen = 0
        for key in headers.keys():
            value = headers[key]
            headersLen = headersLen + len(key)
            headersLen = headersLen + len(value)
            headersLen = headersLen + 4
        
        payloadLength = len(data)
        headerLength = headersLen
        messageLength = 16 + payloadLength + headerLength

        # total
        resultData = bytearray()
        messageLengthToEncode = messageLength
        resultBytes = (messageLengthToEncode).to_bytes(4, byteorder='big')
        resultData = resultData + bytearray(resultBytes)

        # header
        headerLengthToEncode = headerLength
        resultBytes = (headerLengthToEncode).to_bytes(4, byteorder='big')
        resultData = resultData + bytearray(resultBytes)

        # total crc
        crcInt = self.produceCRC32(resultData)
        resultBytes = (crcInt).to_bytes(4, byteorder='big')
        resultData = resultData + bytearray(resultBytes)

        # headers chunk
        for key in headers.keys():
            value = headers[key]
            # header length
            headerKeyLen = len(key)
            headerValLen = len(value)

            resultBytes = (headerKeyLen).to_bytes(1, byteorder='big')
            resultData = resultData + bytearray(resultBytes)

            # header
            headerData = key.encode()
            resultData = resultData + bytearray(headerData)

            # headerType
            headerType = 7
            resultBytes = (headerType).to_bytes(1, byteorder='big')
            resultData = resultData + bytearray(resultBytes)

            # header value length
            resultBytes = (headerValLen).to_bytes(2, byteorder='big')
            resultData = resultData + bytearray(resultBytes)

            # header value
            headerValueData = value.encode()
            resultData = resultData + bytearray(headerValueData)

        # data       
        resultData = resultData + bytearray(data)

        crcInt = self.produceCRC32(resultData)
        resultBytes = (crcInt).to_bytes(4, byteorder='big')
        resultData = resultData + bytearray(resultBytes)

        return resultData























