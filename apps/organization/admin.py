from django.contrib import admin
from django.db.models import Count

from deep.admin import document_preview, linkify
from organization.models import (
    OrganizationType,
    Organization,
)


@admin.register(OrganizationType)
class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_organization_count',)
    search_fields = ('title',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(organization_count=Count('organization'))

    def get_organization_count(self, instance):
        if instance:
            return instance.organization_count
    get_organization_count.short_description = 'Organization Count'


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    search_fields = ('title', 'short_name', 'long_name')
    list_display = ('title', 'short_name', linkify('organization_type'),)
    readonly_fields = (document_preview('logo', 'Logo Preview'),)
    list_filter = ('organization_type',)
    autocomplete_fields = (
        'created_by', 'modified_by', 'logo', 'organization_type', 'regions',
    )
