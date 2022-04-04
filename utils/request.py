from typing import Union
import re

from dataclasses import dataclass, field
import requests

from django.core.files.base import ContentFile


def requesthelper_ignore_error(func):
    def wrapper(self, *args, **kwargs):
        if self.ignore_error and self.error_on_response:
            return
        return func(self, *args, **kwargs)
    return wrapper


@dataclass
class RequestHelper:
    url: str
    ignore_error: bool = False
    response: Union[None, requests.Response] = field(init=False, repr=False)
    error_on_response: Union[bool, None] = field(init=False)

    def __post_init__(self):
        self.fetch()

    @staticmethod
    def sanitize_text(text: str):
        # Remove NUL (0x00) characters
        text = text.replace('\x00', '')
        # Tabs and nbsps to space
        text = re.sub(r'(\t|&nbsp;)', ' ', text)
        # Single line breaks to spaces
        text = re.sub(r'(?<!\n)[ \t]*\n[ \t]*(?!\n)', ' ', text)
        # Multiple spaces to single
        text = re.sub(r' +', ' ', text)
        # More than 3 line breaks to just 3 line breaks
        text = re.sub(r'\n\s*\n\s*(\n\s*)+', '\n\n\n', text)
        return text.strip()

    def fetch(self):
        try:
            self.response = requests.get(self.url)
            self.error_on_response = False
        except Exception:
            self.error_on_response = True
            if not self.ignore_error:
                raise
        return self

    @requesthelper_ignore_error
    def get_file(self) -> Union[ContentFile, None]:
        if self.response:
            return ContentFile(self.response.content)

    @requesthelper_ignore_error
    def get_text(self, sanitize=False) -> Union[str, None]:
        if self.response:
            if sanitize:
                return self.sanitize_text(self.response.text)
            return self.response.text
