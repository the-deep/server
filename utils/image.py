import base64
import uuid
import imghdr
from django.core.files.base import ContentFile


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
