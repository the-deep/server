import json

from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder


DOCX_MIME_TYPE = \
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
PDF_MIME_TYPE = \
    'application/pdf'
EXCEL_MIME_TYPE = \
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
JSON_MIME_TYPE = \
    'application/json'


class Exporter:
    def export(self):
        raise Exception("Not implemented")


class JsonExporter(Exporter):
    def __init__(self):
        self.data = {}

    def export(self):
        """
        Export and save in export_entity
        """
        json_data = json.dumps(
            self.data, sort_keys=True, indent=2,
            cls=DjangoJSONEncoder
        ).encode('utf-8')
        return ContentFile(json_data)
