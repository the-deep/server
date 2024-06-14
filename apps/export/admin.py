from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin, messages
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from deep.admin import ModelAdmin, document_preview

from .models import Export, GenericExport
from .tasks import export_task

TRIGGER_LIMIT = 5


def trigger_retry(modeladmin, request, queryset):
    for export_id in queryset.values_list("id", flat=True).distinct()[:TRIGGER_LIMIT]:
        export_task.delay(export_id, force=True)
    messages.add_message(
        request,
        messages.INFO,
        mark_safe(
            "Successfully force triggerd retry for exports: <br><hr>"
            + "<br>".join("& {} : {}".format(*value) for value in queryset.values_list("id", "title").distinct()[:TRIGGER_LIMIT])
        ),
    )


trigger_retry.short_description = "Force trigger export process for selected export, limit: {}".format(TRIGGER_LIMIT)


class HaveExecutionTimeFilter(admin.SimpleListFilter):
    class Parameter(models.TextChoices):
        TRUE = "true", _("Yes")
        FALSE = "false", _("False")

    title = _("Have Execution Time")
    parameter_name = "have_execution_time"

    def lookups(self, *_):
        return self.Parameter.choices

    def queryset(self, _, queryset):
        _filter = models.Q(started_at__isnull=False, ended_at__isnull=False)
        if self.value() == self.Parameter.TRUE:
            return queryset.filter(_filter)
        if self.value() == self.Parameter.FALSE:
            return queryset.exclude(_filter)
        return queryset


@admin.register(Export)
class ExportAdmin(ModelAdmin):
    list_display = (
        "title",
        "file",
        "type",
        "exported_by",
        "exported_at",
        "execution_time",
        "project",
        "export_type",
        "format",
        "is_preview",
        "status",
    )
    search_fields = ("title",)
    readonly_fields = (document_preview("file"),)
    list_filter = (
        "type",
        "export_type",
        "format",
        "status",
        "is_preview",
        "is_deleted",
        "is_archived",
        ("ended_at", admin.EmptyFieldListFilter),
        HaveExecutionTimeFilter,
        AutocompleteFilterFactory("Project", "project"),
        AutocompleteFilterFactory("Analysis Framework", "project__analysis_framework"),
        AutocompleteFilterFactory("Exported By", "exported_by"),
    )
    actions = [trigger_retry]
    autocomplete_fields = (
        "project",
        "exported_by",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(execution_time=models.F("ended_at") - models.F("started_at"))
            .select_related("exported_by", "project")
        )

    @admin.display(
        ordering="execution_time",
        description="Execution Time",
    )
    def execution_time(self, obj):
        return obj.execution_time


@admin.register(GenericExport)
class GenericExportAdmin(ModelAdmin):
    list_display = (
        "title",
        "file",
        "type",
        "exported_by",
        "exported_at",
        "execution_time",
        "format",
        "status",
    )
    search_fields = ("title",)
    readonly_fields = (document_preview("file"),)
    list_filter = (
        "type",
        "format",
        "status",
        ("ended_at", admin.EmptyFieldListFilter),
        HaveExecutionTimeFilter,
        AutocompleteFilterFactory("Exported By", "exported_by"),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(execution_time=models.F("ended_at") - models.F("started_at"))
            .select_related("exported_by")
        )

    @admin.display(
        ordering="execution_time",
        description="Execution Time",
    )
    def execution_time(self, obj):
        return obj.execution_time
