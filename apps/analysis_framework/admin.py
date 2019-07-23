from django.contrib import admin
from analysis_framework.models import (
    AnalysisFramework,
    AnalysisFrameworkRole,
    AnalysisFrameworkMembership,
    Widget, Filter,
    Exportable,
)

from deep.admin import VersionAdmin, StackedInline


class AnalysisFrameworkMemebershipInline(admin.TabularInline):
    model = AnalysisFrameworkMembership
    extra = 0


class WidgetInline(StackedInline):
    model = Widget


class FilterInline(StackedInline):
    model = Filter


class ExportableInline(StackedInline):
    model = Exportable


@admin.register(AnalysisFramework)
class AnalysisFrameworkAdmin(VersionAdmin):
    inlines = [AnalysisFrameworkMemebershipInline,
               WidgetInline, FilterInline, ExportableInline]

    def has_add_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return ['is_private']


class AnalysisFrameworkRoleAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return ['is_private_role']


admin.site.register(AnalysisFrameworkRole, AnalysisFrameworkRoleAdmin)
