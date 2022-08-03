import json

from django.core.serializers.json import DjangoJSONEncoder


DOCX_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
PDF_MIME_TYPE = 'application/pdf'
EXCEL_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
JSON_MIME_TYPE = 'application/json'


class Exporter:
    def export(self, *_):
        raise Exception("Not implemented")


class JsonExporter(Exporter):
    def __init__(self):
        self.data = {}

    def export(self, filename):
        """
        Export and save in export_entity
        """
        with open(filename, 'w') as fp:
            json.dump(
                self.data,
                fp,
                sort_keys=True,
                cls=DjangoJSONEncoder,
            )
