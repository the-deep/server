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


class FilterDataInline(admin.StackedInline):
    model = FilterData


class ExportDataInline(admin.StackedInline):
    model = ExportData


@admin.register(Entry)
class EntryAdmin(VersionAdmin):
    inlines = [AttributeInline, FilterDataInline, ExportDataInline]
