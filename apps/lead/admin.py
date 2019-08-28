from django.contrib import admin
from reversion.admin import VersionAdmin
from .models import (
    Lead, LeadGroup,
    LeadPreview, LeadPreviewImage,
    EMMEntity,
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
    filter_horizontal = ('assignee',)
    autocomplete_fields = (
        'project', 'created_by', 'modified_by', 'attachment',
    )


@admin.register(LeadGroup)
class LeadGroupAdmin(VersionAdmin):
    pass


@admin.register(EMMEntity)
class EMMEntityAdmin(admin.ModelAdmin):
    pass
