from django.contrib import admin
from organization.models import (
    OrganizationType,
    Organization,
)


admin.site.register(OrganizationType)


def set_donor(modeladmin, request, queryset):
    queryset.update(donor=True)


def reset_donor(modeladmin, request, queryset):
    queryset.update(donor=False)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    actions = [set_donor, reset_donor]
