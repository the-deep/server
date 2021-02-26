from django.contrib import admin
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.db import models
from django.contrib.postgres.aggregates import StringAgg

from reversion.admin import VersionAdmin

from deep.admin import linkify
from lead.models import Lead
from entry.models import Entry
from ary.models import Assessment

from .tasks import generate_viz_stats, generate_project_stats_cache
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


def trigger_project_viz_stat_calc(generator):
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


def trigger_project_stat_cache_calc():
    def action(modeladmin, request, queryset):
        generate_project_stats_cache.delay(force=True)
        messages.add_message(
            request, messages.INFO,
            mark_safe(
                'Successfully triggered Project Stats Cache Calculation for projects.'
            )
        )
    action.short_description = 'Trigger project stat cache calculation'
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
        'associated_regions',
        'entries_count', 'assessment_count', 'members_count',
    ]
    autocomplete_fields = (
        'analysis_framework', 'assessment_template', 'category_editor',
        'created_by', 'modified_by', 'regions',
    )
    list_filter = ('assessment_template',)
    actions = [trigger_project_stat_cache_calc()]
    inlines = [ProjectMembershipInline,
               ProjectUserGroupMembershipInline,
               ProjectJoinRequestInline,
               ProjectOrganizationInline]

    def get_queryset(self, request):
        def _count_subquery(Model, count_field='id'):
            return models.functions.Coalesce(
                models.Subquery(
                    Model.objects.filter(
                        project=models.OuterRef('pk'),
                    ).order_by().values('project')
                    .annotate(c=models.Count('id', distinct=True)).values('c')[:1],
                    output_field=models.IntegerField(),
                ), 0)

        return super().get_queryset(request).prefetch_related(
            'category_editor', 'analysis_framework', 'assessment_template',
        ).annotate(
            leads_count=_count_subquery(Lead),
            entries_count=_count_subquery(Entry),
            assessment_count=_count_subquery(Assessment),
            members_count=_count_subquery(ProjectMembership, count_field='member'),
            associated_regions_count=models.Count('regions', distinct=True),
            associated_regions=StringAgg('regions__title', ',', distinct=True),
        )

    def get_readonly_fields(self, request, obj=None):
        # editing an existing object
        if obj:
            return self.readonly_fields + ('is_private', )
        return self.readonly_fields

    def entries_count(self, obj):
        return obj.entries_count

    def leads_count(self, obj):
        return obj.leads_count

    def assessment_count(self, obj):
        return obj.assessment_count

    def members_count(self, obj):
        return obj.members_count

    entries_count.admin_order_field = 'entries_count'
    leads_count.admin_order_field = 'leads_count'
    assessment_count.admin_order_field = 'assessment_count'
    members_count.admin_order_field = 'members_count'

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
    actions = [trigger_project_viz_stat_calc(generate_viz_stats)]
    autocomplete_fields = ('project',)
    readonly_fields = (AF,)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('project', 'project__analysis_framework')
