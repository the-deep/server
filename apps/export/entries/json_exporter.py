from utils.files import generate_json_file_for_upload
from analysis_framework.models import Widget
from export.models import Export


class JsonExporter:
    def __init__(self, is_preview=False):
        self.is_preview = is_preview
        self.data = {}

    def load_exportables(self, exportables, analysis_framework):
        # get all widget key name in list
        widgets_key = Widget.objects.filter(analysis_framework=analysis_framework).values_list(
            'key',
            flat=True
        )
        # exclude widgets_key which are not in exportables table
        self.exportables = exportables.filter(widget_key__in=widgets_key)
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
        return generate_json_file_for_upload(
            self.data,
            sort_keys=True,
            indent=2,
        )
