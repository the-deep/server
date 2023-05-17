from typing import Dict, List, Tuple, Union, IO
import json

from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder


def generate_file_for_upload(file: IO):
    file.seek(0)
    return ContentFile(
        file.read().encode('utf-8')
    )


def generate_json_file_for_upload(data: Union[Dict, List, Tuple], **kwargs):
    return ContentFile(
        json.dumps(
            data,
            cls=DjangoJSONEncoder,
            **kwargs,
        ).encode('utf-8'),
    )
