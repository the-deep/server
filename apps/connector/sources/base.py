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

    def query_leads(self, params, limit=None):
        from connector.serializers import SourceDataSerializer
        data = self.fetch(params)[0]
        return SourceDataSerializer(
            data[:limit] if limit else data,
            many=True,
        ).data
