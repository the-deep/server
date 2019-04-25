from django.contrib import admin
from django.contrib import messages

from deep.admin import ModelAdmin, document_preview

from .models import Export
from .tasks import export_task


TRIGGER_LIMIT = 5


def trigger_retry(modeladmin, request, queryset):
    for export_id in queryset.values_list('id', flat=True).distinct()[:TRIGGER_LIMIT]:
        export_task.delay(export_id)
    messages.add_message(
        request, messages.INFO,
        'Successfully triggerd retry for exports: {}'.format(
            ','.join(
                '{}({})'.format(value[0], value[1])
                for value in queryset.values_list('title', 'id').distinct()[:TRIGGER_LIMIT]
            )
        )
    )


trigger_retry.short_description = 'Trigger export process for selected export, limit: {}'.format(TRIGGER_LIMIT)


@admin.register(Export)
class ExportAdmin(ModelAdmin):
    list_display = ('title', 'file', 'type', 'export_type', 'pending', 'is_preview',)
    search_fields = ('title',)
    readonly_fields = (document_preview('file'),)
    list_filter = ('type', 'export_type', 'pending', 'is_preview',)
    actions = [trigger_retry]
