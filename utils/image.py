import base64
import uuid
import imghdr
from django.core.files.base import ContentFile
import requests


def decode_base64_if_possible(data):
    if not isinstance(data, str):
        return data, None
    if 'data:' not in data or ';base64,' not in data:
        return data, None

    header, data = data.split(';base64,')

    try:
        decoded_file = base64.b64decode(data)
    except TypeError:
        return data, None

    filename = str(uuid.uuid4())[:12]
    ext = imghdr.what(filename, decoded_file)
    complete_filename = '{}.{}'.format(filename, ext)
    data = ContentFile(decoded_file, name=complete_filename)

    return data, header


def download_file_from_url(url):
    """
    Returns a file object form url
    """
    response = requests.get(url)
    # Make base 64 data
    base_64_data = (
        "data:" + response.headers['Content-Type'] + ";" +
        "base64," + base64.b64encode(response.content).decode("utf-8")
    )
    decoded_file, header = decode_base64_if_possible(base_64_data)
    return decoded_file
