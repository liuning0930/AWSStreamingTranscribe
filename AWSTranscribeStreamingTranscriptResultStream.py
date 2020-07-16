import json
from enum import Enum
from AWSTranscribeStreamingModel import AWSTranscribeStreamingTranscriptEvent

class AWSTranscribeStreamingErrorType(Enum):
    AWSTranscribeStreamingErrorUnknown = 0
    AWSTranscribeStreamingErrorBadRequest = 1
    AWSTranscribeStreamingErrorConflict = 2
    AWSTranscribeStreamingErrorInternalFailure = 3
    AWSTranscribeStreamingErrorLimitExceeded = 4

class AWSTranscribeStreamingTranscriptResultStream():
    def __init__(self):
        super().__init__()
        self.badRequestException = None
        self.conflictException = None
        self.internalFailureException = None
        self.limitExceededException = None

        # A parameter of the transcription of the audio stream.
        # Events are sent periodically from Amazon Transcribe to your application.
        # The event can be a partial transcription of a section of the audio stream,
        # or it can be the entire transcription of that portion of the audio stream. 
        self.transcriptEvent = None

        self.errorCodeDictionary = {
            "BadRequestException": (AWSTranscribeStreamingErrorType.AWSTranscribeStreamingErrorBadRequest),
            "ConflictException": (AWSTranscribeStreamingErrorType.AWSTranscribeStreamingErrorConflict),
            "InternalFailureException": (AWSTranscribeStreamingErrorType.AWSTranscribeStreamingErrorInternalFailure),
            "LimitExceededException": (AWSTranscribeStreamingErrorType.AWSTranscribeStreamingErrorLimitExceeded)
        }

    def resultStreamForWSSBody(self, body, headers):
        jsonObject = json.loads(body)
        if not jsonObject:
            return None

        awsResultStream = AWSTranscribeStreamingTranscriptResultStream()
        # Populate error payload
        if headers[':message-type'] == 'exception':
            errorType = headers[":exception-type"]
            self.error(errorType, awsResultStream)
            return awsResultStream

        if headers[':message-type'] == "event":
            transcriptEvent = AWSTranscribeStreamingTranscriptEvent()
            transcriptEvent.parse(jsonObject)
            awsResultStream.transcriptEvent = transcriptEvent
            return awsResultStream

        assert(False, 'Unable to deserialize event body into an exception or TranscriptEvent')
        return None

    def error(self, errorType, awsResultStream):
        errorEnum = self.errorCodeDictionary[errorType]
        if errorEnum == AWSTranscribeStreamingErrorType.AWSTranscribeStreamingErrorBadRequest:
            awsResultStream.badRequestException = errorType
        elif errorEnum == AWSTranscribeStreamingErrorType.AWSTranscribeStreamingErrorConflict:
            awsResultStream.conflictException = errorType
        elif errorEnum == AWSTranscribeStreamingErrorType.AWSTranscribeStreamingErrorInternalFailure:
            awsResultStream.internalFailureException = errorType
        elif errorEnum == AWSTranscribeStreamingErrorType.AWSTranscribeStreamingErrorLimitExceeded:
            awsResultStream.limitExceededException = errorType
