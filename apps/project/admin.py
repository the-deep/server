from django.contrib import admin
from reversion.admin import VersionAdmin
from .models import (
    Project,
    ProjectRole,
    ProjectMembership,
    ProjectUserGroupMembership,
    ProjectStatus,
    ProjectStatusCondition,
    ProjectJoinRequest,
)


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 0


class ProjectUserGroupMembershipInline(admin.TabularInline):
    model = ProjectUserGroupMembership
    extra = 0


class ProjectJoinRequestInline(admin.TabularInline):
    model = ProjectJoinRequest
    extra = 0


@admin.register(Project)
class ProjectAdmin(VersionAdmin):
    search_fields = ['title']
    list_display = [
        'title', 'category_editor', 'analysis_framework',
        'assessment_template', 'members_count', 'associated_regions',
    ]
    list_filter = ('assessment_template',)
    inlines = [ProjectMembershipInline,
               ProjectUserGroupMembershipInline,
               ProjectJoinRequestInline]

    def members_count(self, obj):
        return obj.members.count()

    def associated_regions(self, obj):
        if obj.regions.count() == 0:
            return None
        return ', '.join(r.title for r in obj.regions.all())


class ProjectConditionInline(admin.StackedInline):
    model = ProjectStatusCondition
    extra = 0


@admin.register(ProjectStatus)
class ProjectStatusAdmin(admin.ModelAdmin):
    inlines = [ProjectConditionInline]


admin.site.register(ProjectRole)
