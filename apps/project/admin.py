import json

from admin_auto_filters.filters import AutocompleteFilterFactory
from assessment_registry.models import AssessmentRegistry
from django.contrib import admin, messages
from django.contrib.postgres.aggregates import StringAgg
from django.db import models
from django.utils.safestring import mark_safe
from entry.models import Entry
from lead.models import Lead
from reversion.admin import VersionAdmin

from deep.admin import linkify

from .forms import ProjectRoleForm
from .models import (
    Project,
    ProjectChangeLog,
    ProjectJoinRequest,
    ProjectMembership,
    ProjectOrganization,
    ProjectPinned,
    ProjectRole,
    ProjectStats,
    ProjectUserGroupMembership,
)
from .tasks import generate_project_stats_cache, generate_viz_stats

TRIGGER_LIMIT = 5


def trigger_project_viz_stat_calc(generator):
    def action(modeladmin, request, queryset):
        for project_id in queryset.values_list("project_id", flat=True).distinct()[:TRIGGER_LIMIT]:
            generator.delay(project_id, force=True)
        messages.add_message(
            request,
            messages.INFO,
            mark_safe(
                "Successfully triggered Project Stats Calculation for projects: <br><hr>"
                + "<br>".join(
                    "* {0} : {1}".format(*value)
                    for value in queryset.values_list("project_id", "project__title").distinct()[:TRIGGER_LIMIT]
                )
            ),
        )

    action.short_description = "Trigger project stat calculation"
    return action


def trigger_project_stat_cache_calc():
    def action(modeladmin, request, queryset):
        generate_project_stats_cache.delay(force=True)
        messages.add_message(
            request, messages.INFO, mark_safe("Successfully triggered Project Stats Cache Calculation for projects.")
        )

    action.short_description = "Trigger project stat cache calculation"
    return action


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 0
    autocomplete_fields = (
        "added_by",
        "linked_group",
        "member",
    )


class ProjectUserGroupMembershipInline(admin.TabularInline):
    model = ProjectUserGroupMembership
    extra = 0
    autocomplete_fields = (
        "added_by",
        "usergroup",
    )


class ProjectOrganizationInline(admin.TabularInline):
    model = ProjectOrganization
    autocomplete_fields = ("organization",)


class ProjectJoinRequestInline(admin.TabularInline):
    model = ProjectJoinRequest
    extra = 0
    autocomplete_fields = (
        "requested_by",
        "responded_by",
    )


@admin.register(Project)
class ProjectAdmin(VersionAdmin):
    search_fields = ["title"]
    list_display = [
        "title",
        linkify("category_editor", "Category Editor"),
        linkify("analysis_framework", "Assessment Framework"),
        linkify("assessment_template", "Assessment Template"),
        "associated_regions",
        "entries_count",
        "assessment_count",
        "members_count",
        "deleted_at",
    ]
    autocomplete_fields = (
        "analysis_framework",
        "assessment_template",
        "category_editor",
        "created_by",
        "modified_by",
        "regions",
    )
    list_filter = (
        "assessment_template",
        "is_private",
        "is_deleted",
    )
    actions = [trigger_project_stat_cache_calc()]
    inlines = [ProjectMembershipInline, ProjectUserGroupMembershipInline, ProjectJoinRequestInline, ProjectOrganizationInline]

    def get_queryset(self, request):
        def _count_subquery(Model, count_field="id"):
            return models.functions.Coalesce(
                models.Subquery(
                    Model.objects.filter(
                        project=models.OuterRef("pk"),
                    )
                    .order_by()
                    .values("project")
                    .annotate(c=models.Count("id", distinct=True))
                    .values("c")[:1],
                    output_field=models.IntegerField(),
                ),
                0,
            )

        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                "category_editor",
                "analysis_framework",
                "assessment_template",
            )
            .annotate(
                leads_count=_count_subquery(Lead),
                entries_count=_count_subquery(Entry),
                assessment_count=_count_subquery(AssessmentRegistry),
                members_count=_count_subquery(ProjectMembership, count_field="member"),
                associated_regions_count=models.Count("regions", distinct=True),
                associated_regions=StringAgg("regions__title", ",", distinct=True),
            )
        )

    def get_readonly_fields(self, request, obj=None):
        # editing an existing object
        if obj:
            return self.readonly_fields + ("is_private",)
        return self.readonly_fields

    def entries_count(self, obj):
        return obj.entries_count

    def leads_count(self, obj):
        return obj.leads_count

    def assessment_count(self, obj):
        return obj.assessment_count

    def members_count(self, obj):
        return obj.members_count

    entries_count.admin_order_field = "entries_count"
    leads_count.admin_order_field = "leads_count"
    assessment_count.admin_order_field = "assessment_count"
    members_count.admin_order_field = "members_count"

    def associated_regions(self, obj):
        count = obj.associated_regions_count
        regions = obj.associated_regions
        if count == 0:
            return ""
        elif count == 1:
            return regions
        return f"{regions[:10]}.... ({count})"


@admin.register(ProjectRole)
class ProjectRoleAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "level", "type", "is_default_role")
    form = ProjectRoleForm


@admin.register(ProjectStats)
class ProjectEntryStatsAdmin(admin.ModelAdmin):
    AF = linkify("project.analysis_framework", "AF")

    search_fields = ("project__title",)
    list_filter = ("status",)
    list_display = (
        "project",
        "modified_at",
        AF,
        "status",
        "file",
        "confidential_file",
    )
    actions = [trigger_project_viz_stat_calc(generate_viz_stats)]
    autocomplete_fields = ("project",)
    readonly_fields = (AF, "token")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("project", "project__analysis_framework")


@admin.register(ProjectChangeLog)
class ProjectChangeLogAdmin(admin.ModelAdmin):
    search_fields = ("project__title",)
    list_filter = (
        AutocompleteFilterFactory("Project", "project"),
        AutocompleteFilterFactory("User", "user"),
        "action",
        "created_at",
    )
    list_display = (
        "project",
        "created_at",
        "action",
        "user",
    )
    autocomplete_fields = (
        "project",
        "user",
    )
    readonly_fields = ("project", "created_at", "action", "user", "diff", "diff_pretty")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                "project",
                "user",
            )
        )

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Diff pretty JSON")
    def diff_pretty(self, obj):
        return mark_safe(f"<pre>{json.dumps(obj.diff, indent=2)}</pre>")


@admin.register(ProjectPinned)
class ProjectPinnedAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "user", "order")
