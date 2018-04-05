from abc import ABC, abstractmethod


class SourceData:
    def __init__(self, title, published_on, source,
                 url=None, text=None, **kwargs):
        self.title = title
        self.published_on = published_on
        self.source = source
        self.url = url
        self.text = text
        self.extra = kwargs


class Source(ABC):
    def __init__(self):
        if not hasattr(self, 'title') \
                or not hasattr(self, 'key') \
                or not hasattr(self, 'options'):
            raise Exception('Source not defined properly')

    @abstractmethod
    def fetch(params, page=None, limit=None):
        pass
