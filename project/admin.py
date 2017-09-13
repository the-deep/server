from django.contrib import admin
from reversion.admin import VersionAdmin
from .models import Project, ProjectMembership


class ProjectInline(admin.TabularInline):
    model = ProjectMembership


@admin.register(Project)
class ProjectAdmin(VersionAdmin):
    inlines = [ProjectInline]
