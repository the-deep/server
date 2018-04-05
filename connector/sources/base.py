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
