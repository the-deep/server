from django.contrib import admin
from analysis_framework.models import (
    AnalysisFramework,
    Widget, Filter,
    Exportable,
)

from deep.admin import VersionAdmin, StackedInline


class WidgetInline(StackedInline):
    model = Widget


class FilterInline(StackedInline):
    model = Filter


class ExportableInline(StackedInline):
    model = Exportable


@admin.register(AnalysisFramework)
class AnalysisFrameworkAdmin(VersionAdmin):
    inlines = [WidgetInline, FilterInline, ExportableInline]
