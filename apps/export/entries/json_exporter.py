from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder

from export.mime_types import JSON_MIME_TYPE
from analysis_framework.models import Widget
from utils.common import generate_filename
from export.models import Export

import json


class JsonExporter:
    def __init__(self, is_preview=False):
        self.is_preview = is_preview
        self.data = {}

    def load_exportables(self, exportables):
        self.exportables = exportables
        self.widget_ids = []

        self.data['widgets'] = []
        for exportable in self.exportables:
            widget = Widget.objects.get(
                analysis_framework=exportable.analysis_framework,
                key=exportable.widget_key,
            )
            self.widget_ids.append(widget.id)

            data = {}
            data['id'] = widget.key
            data['widget_type'] = widget.widget_id
            data['title'] = widget.title
            data['properties'] = widget.properties
            self.data['widgets'].append(data)

        return self

    def add_entries(self, entries):
        self.data['entries'] = []

        iterable_entries = entries[:Export.PREVIEW_ENTRY_SIZE] if self.is_preview else entries
        for entry in iterable_entries:
            lead = entry.lead
            data = {}
            data['id'] = entry.id
            data['lead_id'] = lead.id
            data['lead'] = lead.title
            data['source'] = lead.get_source_display()
            data['priority'] = lead.get_priority_display()
            data['author'] = lead.get_authors_display()
            data['date'] = lead.published_on
            data['excerpt'] = entry.excerpt
            data['image'] = entry.get_image_url()
            data['attributes'] = []
            data['data_series'] = {}

            for attribute in entry.attribute_set.all():
                attribute_data = {}
                attribute_data['widget_id'] = attribute.widget.key
                attribute_data['data'] = attribute.data
                data['attributes'].append(attribute_data)
            if entry.tabular_field:
                data['data_series'] = {
                    'options': entry.tabular_field.options,
                    'data': entry.tabular_field.actual_data,
                }
            self.data['entries'].append(data)
        return self

    def export(self):
        """
        Export and return export data
        """
        filename = generate_filename('Entries JSON Export', 'json')
        json_data = json.dumps(self.data, sort_keys=True, indent=2,
                               cls=DjangoJSONEncoder).encode('utf-8')

        return filename, Export.JSON, JSON_MIME_TYPE, ContentFile(json_data)
