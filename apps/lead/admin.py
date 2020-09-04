from django.contrib import admin
from reversion.admin import VersionAdmin
from django.utils.safestring import mark_safe
from django.contrib import messages
from admin_auto_filters.filters import AutocompleteFilterFactory

from .tasks import extract_from_lead
from .models import (
    Lead, LeadGroup,
    LeadPreview, LeadPreviewImage,
    EMMEntity,
)


class LeadPreviewInline(admin.StackedInline):
    model = LeadPreview


class LeadPreviewImageInline(admin.TabularInline):
    model = LeadPreviewImage
    extra = 0


def trigger_lead_extract(modeladmin, request, queryset):
    extract_from_lead.delay(
        list(queryset.values_list('id', flat=True).distinct()[:10])
    )
    messages.add_message(
        request, messages.INFO,
        mark_safe(
            'Successfully triggered leads: <br><hr>' +
            '<br>'.join(
                '* {0} : ({1}) {2}'.format(*value)
                for value in queryset.values_list('id', 'project_id', 'title').distinct()
            )
        )
    )


trigger_lead_extract.short_description = 'Trigger lead extraction'


@admin.register(Lead)
class LeadAdmin(VersionAdmin):
    inlines = [LeadPreviewInline, LeadPreviewImageInline]
    search_fields = ['title']
    list_filter = (
        AutocompleteFilterFactory('Project', 'project'),
        AutocompleteFilterFactory('Created by', 'created_by'),
        'created_at'
    )
    list_display = [
        'title', 'project', 'created_by', 'created_at',
    ]
    ordering = ('project', 'created_by', 'created_at')
    autocomplete_fields = (
        'project', 'created_by', 'modified_by', 'attachment', 'assignee',
        'source', 'authors', 'author', 'emm_entities', 'lead_group',
    )
    actions = [trigger_lead_extract]


@admin.register(LeadGroup)
class LeadGroupAdmin(VersionAdmin):
    search_fields = ('title',)
    autocomplete_fields = ('project', 'created_by', 'modified_by',)


@admin.register(EMMEntity)
class EMMEntityAdmin(admin.ModelAdmin):
    search_fields = ('name',)
