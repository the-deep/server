from django.contrib import admin
from deep.admin import document_preview
from organization.models import (
    OrganizationType,
    Organization,
)


@admin.register(OrganizationType)
class OrganizationTypeAdmin(admin.ModelAdmin):
    search_fields = ('title',)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    search_fields = ('title', 'short_name', 'long_name')
    list_display = ('title', 'short_name', 'organization_type',)
    readonly_fields = (document_preview('logo', 'Logo Preview'),)
    list_filter = ('organization_type',)
    filter_horizontal = ('regions',)
    autocomplete_fields = (
        'created_by', 'modified_by', 'logo', 'organization_type',
    )
