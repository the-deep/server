from django.contrib import admin
from reversion.admin import VersionAdmin
from .models import (
    Lead, LeadGroup,
    LeadPreview, LeadPreviewImage,
)


class LeadPreviewInline(admin.StackedInline):
    model = LeadPreview


class LeadPreviewImageInline(admin.TabularInline):
    model = LeadPreviewImage


@admin.register(Lead)
class LeadAdmin(VersionAdmin):
    inlines = [LeadPreviewInline, LeadPreviewImageInline]
    search_fields = ['title']
    list_filter = ('project', 'created_by', 'created_at')
    list_display = [
        'title', 'project', 'created_by', 'created_at',
    ]
    ordering = ('project', 'created_by', 'created_at')


@admin.register(LeadGroup)
class LeadGroupAdmin(VersionAdmin):
    pass
