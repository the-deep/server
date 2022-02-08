import base64
from typing import Union
from dataclasses import dataclass, field
import requests

from utils.image import decode_base64_if_possible


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
    response: Union[str, None] = field(init=False, repr=False)
    error_on_response: Union[bool, None] = field(init=False)

    def __post_init__(self):
        self.fetch()

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
    def get_decoded_file(self):
        base_64_data = (
            "data:" + self.response.headers['Content-Type'] + ";" +
            "base64," + base64.b64encode(self.response.content).decode("utf-8")
        )
        decoded_file, _ = decode_base64_if_possible(base_64_data)
        return decoded_file

    @requesthelper_ignore_error
    def get_text(self):
        return self.response.text
