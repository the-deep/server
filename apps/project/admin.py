from django.contrib import admin
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.db.models import Count
from django.contrib.postgres.aggregates import StringAgg

from reversion.admin import VersionAdmin
from .tasks import generate_entry_stats
from .forms import ProjectRoleForm
from .models import (
    Project,
    ProjectRole,
    ProjectMembership,
    ProjectUserGroupMembership,
    ProjectEntryStats,
    ProjectStatus,
    ProjectStatusCondition,
    ProjectJoinRequest,
)

TRIGGER_LIMIT = 5


def trigger_project_stat_calc(modeladmin, request, queryset):
    for project_id in queryset.values_list('project_id', flat=True).distinct()[:TRIGGER_LIMIT]:
        generate_entry_stats.delay(project_id, force=True)
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


trigger_project_stat_calc.short_description = 'Trigger project stat calculation'


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 0
    autocomplete_fields = ('added_by', 'linked_group', 'member',)


class ProjectUserGroupMembershipInline(admin.TabularInline):
    model = ProjectUserGroupMembership
    extra = 0
    autocomplete_fields = ('added_by', 'usergroup',)


class ProjectJoinRequestInline(admin.TabularInline):
    model = ProjectJoinRequest
    extra = 0
    autocomplete_fields = ('requested_by', 'responded_by',)


@admin.register(Project)
class ProjectAdmin(VersionAdmin):
    search_fields = ['title']
    list_display = [
        'title', 'category_editor', 'analysis_framework',
        'assessment_template', 'members_count', 'associated_regions',
    ]
    autocomplete_fields = (
        'analysis_framework', 'assessment_template', 'category_editor',
        'created_by', 'modified_by', 'regions',
    )
    list_filter = ('assessment_template',)
    inlines = [ProjectMembershipInline,
               ProjectUserGroupMembershipInline,
               ProjectJoinRequestInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
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


@admin.register(ProjectEntryStats)
class ProjectEntryStatsAdmin(admin.ModelAdmin):
    search_fields = ('project__title',)
    list_filter = ('status',)
    list_display = ('project', 'modified_at', 'status',)
    actions = [trigger_project_stat_calc]
