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


class FilterDataInline(admin.StackedInline):
    model = FilterData
    extra = 0


class ExportDataInline(admin.StackedInline):
    model = ExportData
    extra = 0


@admin.register(Entry)
class EntryAdmin(VersionAdmin):
    custom_inlines = [('attribute', AttributeInline), ('filter', FilterDataInline), ('exportable', ExportDataInline)]
    list_display = [
        'lead', 'project', 'created_by', 'created_at',
        query_buttons('View', [inline[0] for inline in custom_inlines]),
    ]
    list_filter = ('project', 'created_by', 'created_at')
    ordering = ('project', 'created_by', 'created_at')

    def get_inline_instances(self, request, obj=None):
        inlines = []
        for name, inline in self.custom_inlines:
            if request.GET.get(f'show_{name}', 'False').lower() == 'true':
                inlines.append(inline(self.model, self.admin_site))
        return inlines
