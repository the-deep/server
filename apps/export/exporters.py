from utils.files import generate_json_file_for_upload

DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PDF_MIME_TYPE = "application/pdf"
EXCEL_MIME_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
JSON_MIME_TYPE = "application/json"


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
        return generate_json_file_for_upload(
            self.data,
            sort_keys=True,
            indent=2,
        )
