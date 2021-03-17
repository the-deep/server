from django.contrib import admin
from reversion.admin import VersionAdmin
import reversion

from deep.admin import query_buttons

from entry.models import (
    Entry,
    Attribute,
    FilterData,
    ExportData,
    EntryComment,

    # Entry Group
    ProjectEntryLabel,
    LeadEntryGroup,
)


class AttributeInline(admin.StackedInline):
    model = Attribute
    extra = 0
    raw_id_fields = ('widget',)


class EntryCommentInline(admin.TabularInline):
    model = EntryComment
    extra = 0


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
    custom_inlines = [('attribute', AttributeInline),
                      ('filter', FilterDataInline),
                      ('exportable', ExportDataInline),
                      ('Entry Comment', EntryCommentInline),
                      ]
    list_display = [
        'lead', 'project', 'created_by', 'created_at',
        query_buttons('View', [inline[0] for inline in custom_inlines]),
    ]
    search_fields = ('lead__title',)
    list_filter = ('project', 'created_by', 'created_at')
    autocomplete_fields = (
        'lead', 'project', 'created_by', 'modified_by', 'analysis_framework', 'tabular_field',
        'image', 'verification_last_changed_by',
    )
    ordering = ('project', 'created_by', 'created_at')

    def get_queryset(self, request):
        return Entry.objects.prefetch_related('project', 'created_by', 'lead')

    def get_inline_instances(self, request, obj=None):
        inlines = []
        for name, inline in self.custom_inlines:
            if request.GET.get(f'show_{name}', 'False').lower() == 'true':
                inlines.append(inline(self.model, self.admin_site))
        return inlines


@admin.register(ProjectEntryLabel)
class ProjectEntryLabelAdmin(VersionAdmin):
    search_fields = ('title',)
    autocomplete_fields = ('created_by', 'modified_by', 'project')
    list_filter = ('project',)
    list_display = ('__str__', 'color')


reversion.register(LeadEntryGroup)
