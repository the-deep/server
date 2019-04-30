import json

from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder

from export.models import Export
from utils.common import generate_filename

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

    def export(self, export_type):
        """
        Export and save in export_entity
        """
        title = '{} JSON EXPORT'.format(export_type)
        filename = generate_filename(title, 'json')

        json_data = json.dumps(self.data, sort_keys=True, indent=2,
                               cls=DjangoJSONEncoder).encode('utf-8')

        return filename, Export.JSON, JSON_MIME_TYPE, ContentFile(json_data)
