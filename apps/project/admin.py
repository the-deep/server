from django.contrib import admin
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.db.models import Count
from django.contrib.postgres.aggregates import StringAgg
from admin_auto_filters.filters import AutocompleteFilterFactory

from reversion.admin import VersionAdmin

from deep.admin import linkify

from .tasks import generate_stats
from .forms import ProjectRoleForm
from .models import (
    Project,
    ProjectRole,
    ProjectMembership,
    ProjectUserGroupMembership,
    ProjectStats,
    ProjectStatus,
    ProjectStatusCondition,
    ProjectJoinRequest,
    ProjectOrganization,
)

TRIGGER_LIMIT = 5


def trigger_project_stat_calc(generator):
    def action(modeladmin, request, queryset):
        for project_id in queryset.values_list('project_id', flat=True).distinct()[:TRIGGER_LIMIT]:
            generator.delay(project_id, force=True)
        messages.add_message(
            request, messages.INFO,
            mark_safe(
                'Successfully triggered Project Stats Calculation for projects: <br><hr>' +
                '<br>'.join(
                    '* {0} : {1}'.format(*value)
                    for value in queryset.values_list('project_id', 'project__title').distinct()[:TRIGGER_LIMIT]
                )
            )
        )
    action.short_description = 'Trigger project stat calculation'
    return action


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 0
    autocomplete_fields = ('added_by', 'linked_group', 'member',)


class ProjectUserGroupMembershipInline(admin.TabularInline):
    model = ProjectUserGroupMembership
    extra = 0
    autocomplete_fields = ('added_by', 'usergroup',)


class ProjectOrganizationInline(admin.TabularInline):
    model = ProjectOrganization


class ProjectJoinRequestInline(admin.TabularInline):
    model = ProjectJoinRequest
    extra = 0
    autocomplete_fields = ('requested_by', 'responded_by',)


@admin.register(Project)
class ProjectAdmin(VersionAdmin):
    search_fields = ['title']
    list_display = [
        'title',
        linkify('category_editor', 'Category Editor'),
        linkify('analysis_framework', 'Assessment Framework'),
        linkify('assessment_template', 'Assessment Template'),
        'members_count', 'associated_regions',
    ]
    autocomplete_fields = (
        'analysis_framework', 'assessment_template', 'category_editor',
        'created_by', 'modified_by', 'regions',
    )
    list_filter = (AutocompleteFilterFactory('Assessment Template', 'assessment_template'),)
    inlines = [ProjectMembershipInline,
               ProjectUserGroupMembershipInline,
               ProjectJoinRequestInline,
               ProjectOrganizationInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'category_editor', 'analysis_framework', 'assessment_template',
        ).annotate(
            members_count=Count('members', distinct=True),
            associated_regions_count=Count('regions', distinct=True),
            associated_regions=StringAgg('regions__title', ',', distinct=True),
        )

    def get_readonly_fields(self, request, obj=None):
        # editing an existing object
        if obj:
            return self.readonly_fields + ('is_private', )
        return self.readonly_fields

    def members_count(self, obj):
        return obj.members_count

    def associated_regions(self, obj):
        count = obj.associated_regions_count
        regions = obj.associated_regions
        if count == 0:
            return ''
        elif count == 1:
            return regions
        return f'{regions[:10]}.... ({count})'


class ProjectConditionInline(admin.StackedInline):
    model = ProjectStatusCondition
    extra = 0


@admin.register(ProjectStatus)
class ProjectStatusAdmin(admin.ModelAdmin):
    inlines = [ProjectConditionInline]


@admin.register(ProjectRole)
class ProjectRoleAdmin(admin.ModelAdmin):
    form = ProjectRoleForm


@admin.register(ProjectStats)
class ProjectEntryStatsAdmin(admin.ModelAdmin):
    AF = linkify('project.analysis_framework', 'AF')

    search_fields = ('project__title',)
    list_filter = ('status',)
    list_display = ('project', 'modified_at', AF, 'status', 'file', 'confidential_file',)
    actions = [trigger_project_stat_calc(generate_stats)]
    autocomplete_fields = ('project',)
    readonly_fields = (AF,)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('project', 'project__analysis_framework')
