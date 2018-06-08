from django.contrib import admin
from reversion.admin import VersionAdmin
from .models import (
    Project,
    ProjectMembership,
    ProjectStatus,
    ProjectStatusCondition,
    ProjectJoinRequest,
)


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 0


class ProjectJoinRequestInline(admin.TabularInline):
    model = ProjectJoinRequest
    extra = 0


@admin.register(Project)
class ProjectAdmin(VersionAdmin):
    inlines = [ProjectMembershipInline, ProjectJoinRequestInline]


class ProjectConditionInline(admin.StackedInline):
    model = ProjectStatusCondition
    extra = 0


@admin.register(ProjectStatus)
class ProjectStatusAdmin(admin.ModelAdmin):
    inlines = [ProjectConditionInline]
