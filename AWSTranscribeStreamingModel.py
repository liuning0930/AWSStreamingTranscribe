from enum import Enum

class AWSTranscribeStreamingItemType(Enum):
    AWSTranscribeStreamingItemTypeUnknown = 0
    AWSTranscribeStreamingItemTypePronunciation = 1
    AWSTranscribeStreamingItemTypePunctuation = 2

class AWSTranscribeStreamingItem():
    def __init__(self):
        super().__init__()
        self.content = ""
        self.endTime = 0.0
        self.startTime = 0.0
        self.types = 0
        self.vocabularyFilterMatch = False

    def assignTypes(self, type):
        if type.upper() == 'PRONUNCIATION':
            self.types = AWSTranscribeStreamingItemType.AWSTranscribeStreamingItemTypePronunciation
        elif type.upper() == 'PUNCTUATION':
            self.types = AWSTranscribeStreamingItemType.AWSTranscribeStreamingItemTypePunctuation
        else:
            self.types = AWSTranscribeStreamingItemType.AWSTranscribeStreamingItemTypeUnknown

class AWSTranscribeStreamingAlternative():
    def __init__(self):
        super().__init__()
        self.items = []
        self.transcript = ""

class AWSTranscribeStreamingResult():
    def __init__(self):
        super().__init__()
        self.alternatives = []
        self.endTime = 0.0
        self.isPartial = False
        self.resultId = ""
        self.startTime = 0.0

class AWSTranscribeStreamingTranscript():
    def __init__(self):
        super().__init__()
        self.results = []

class AWSTranscribeStreamingTranscriptEvent():
    def __init__(self):
        super().__init__()
        self.results = []

    def parse(self, transcriptBody):
        results = transcriptBody['Transcript']['Results']
        tempResults = []
        if len(results) > 0:
            for result in results:
                transcribeResult = AWSTranscribeStreamingResult()

                alternatives = result['Alternatives']
                transcribeAlternatives = self.parseAlternatives(alternatives)
                transcribeResult.alternatives = transcribeAlternatives
                transcribeResult.endTime = result['EndTime']
                transcribeResult.isPartial = bool(result['IsPartial'])
                transcribeResult.resultId = result['ResultId']
                transcribeResult.startTime = result['StartTime']
                tempResults.append(transcribeResult)
        self.results = tempResults

    def parseAlternatives(self, alternatives):
        transcribeAlternatives = []
        for alternative in alternatives:
            transcribeAlternative = AWSTranscribeStreamingAlternative()
            items = alternative['Items']
            transcribeAlternativeItems = []
            for item in items:
                transcribeItem = AWSTranscribeStreamingItem()
                transcribeItem.content = item['Content']
                transcribeItem.endTime = item['EndTime']
                transcribeItem.startTime = item['StartTime']
                transcribeItem.assignTypes(item['Type'])
                transcribeAlternativeItems.append(transcribeItem)
            transcribeAlternative.items = transcribeAlternativeItems
            transcribeAlternatives.append(transcribeAlternative)

        return transcribeAlternatives

class AWSTranscribeStreamingModel():
    def __init__(self):
        super().__init__()
            
