from abc import ABC, abstractmethod


class Source(ABC):
    def __init__(self):
        if not hasattr(self, 'title') \
                or not hasattr(self, 'key') \
                or not hasattr(self, 'options'):
            raise Exception('Source not defined properly')

    @abstractmethod
    def fetch(params, page=None, limit=None):
        pass

    def query_leads(self, params):
        from connector.serializers import SourceDataSerializer
        return SourceDataSerializer(
            self.fetch(params)[0],
            many=True,
        ).data
