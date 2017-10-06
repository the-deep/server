from django.contrib import admin
from reversion.admin import VersionAdmin
from analysis_framework.models import (
    AnalysisFramework,
    Widget, Filter,
    Exportable,
)


class WidgetInline(admin.StackedInline):
    model = Widget


class FilterInline(admin.StackedInline):
    model = Filter


class ExportableInline(admin.StackedInline):
    model = Exportable


@admin.register(AnalysisFramework)
class AnalysisFrameworkAdmin(VersionAdmin):
    inlines = [WidgetInline, FilterInline, ExportableInline]
