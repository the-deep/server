import json
from dataclasses import dataclass, field
from typing import Callable, Dict, Union

import requests
from django.core.files.base import ContentFile

from utils.common import sanitize_text


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
    custom_error_handler: Union[Callable, None] = None
    response: Union[None, requests.Response] = field(init=False, repr=False)
    error_on_response: Union[bool, None] = field(init=False)

    def __post_init__(self):
        self.fetch()

    @staticmethod
    def sanitize_text(text: str):
        return sanitize_text(text)

    def fetch(self):
        try:
            self.response = requests.get(self.url)
            self.error_on_response = False
        except Exception as e:
            self.error_on_response = True
            if self.custom_error_handler:
                self.custom_error_handler(e, url=self.url)
            if not self.ignore_error:
                raise e
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

    @requesthelper_ignore_error
    def json(self) -> Union[Dict, None]:
        if self.response:
            try:
                return self.response.json()
            except json.decoder.JSONDecodeError as e:
                if self.custom_error_handler is None:
                    raise e
                self.custom_error_handler(e, url=self.url)
