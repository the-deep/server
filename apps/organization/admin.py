from django.contrib import admin
from organization.models import (
    OrganizationType,
    Organization,
)

admin.site.register(OrganizationType)

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    search_fields = ('title', 'short_name', 'long_name')
    list_display = ('title', 'short_name', 'organization_type',)
    list_filter = ('organization_type',)
