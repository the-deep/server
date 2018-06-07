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

    def export(self, export_entity):
        """
        Export and save in export_entity
        """
        title = '{} JSON EXPORT'.format(export_entity.type.title())
        filename = generate_filename(title, 'json')
        export_entity.file.save(filename, ContentFile(
            json.dumps(self.data, sort_keys=True, indent=2,
                       cls=DjangoJSONEncoder)
        ))

        export_entity.format = Export.JSON
        export_entity.mime_type = JSON_MIME_TYPE

        export_entity.title = filename
        export_entity.pending = False

        export_entity.save()
