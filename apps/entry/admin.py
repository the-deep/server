from django.contrib import admin
from reversion.admin import VersionAdmin

from deep.admin import query_buttons

from entry.models import (
    Entry,
    Attribute,
    FilterData,
    ExportData,
)


class AttributeInline(admin.StackedInline):
    model = Attribute
    extra = 0
    raw_id_fields = ('widget',)


class FilterDataInline(admin.StackedInline):
    model = FilterData
    extra = 0
    raw_id_fields = ('filter',)


class ExportDataInline(admin.StackedInline):
    model = ExportData
    extra = 0
    raw_id_fields = ('exportable',)


@admin.register(Entry)
class EntryAdmin(VersionAdmin):
    custom_inlines = [('attribute', AttributeInline), ('filter', FilterDataInline), ('exportable', ExportDataInline)]
    list_display = [
        'lead', 'project', 'created_by', 'created_at',
        query_buttons('View', [inline[0] for inline in custom_inlines]),
    ]
    list_filter = ('project', 'created_by', 'created_at')
    autocomplete_fields = (
        'lead', 'project', 'created_by', 'modified_by', 'analysis_framework', 'tabular_field',
    )
    ordering = ('project', 'created_by', 'created_at')

    def get_inline_instances(self, request, obj=None):
        inlines = []
        for name, inline in self.custom_inlines:
            if request.GET.get(f'show_{name}', 'False').lower() == 'true':
                inlines.append(inline(self.model, self.admin_site))
        return inlines
