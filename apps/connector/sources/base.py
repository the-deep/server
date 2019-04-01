from abc import ABC, abstractmethod


class Source(ABC):
    DEFAULT_PER_PAGE = 25

    def __init__(self):
        if not hasattr(self, 'title') \
                or not hasattr(self, 'key') \
                or not hasattr(self, 'options'):
            raise Exception('Source not defined properly')

    @abstractmethod
    def fetch(params, page=None, limit=None):
        pass

    def query_leads(self, params, limit=None, offset=None):
        from connector.serializers import SourceDataSerializer

        if offset is None or offset < 0:
            offset = 0
        if not limit or limit < 0:
            limit = Source.DEFAULT_PER_PAGE

        data = self.fetch(params)[0]
        return SourceDataSerializer(
            data[offset:offset + limit],
            many=True,
        ).data
