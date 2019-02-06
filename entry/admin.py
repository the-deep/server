from django.contrib import admin
from reversion.admin import VersionAdmin
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
    inlines = [AttributeInline, FilterDataInline, ExportDataInline]
    list_display = [
        'lead', 'project', 'created_by', 'created_at',
    ]
    list_filter = ('project', 'created_by', 'created_at')
    ordering = ('project', 'created_by', 'created_at')
