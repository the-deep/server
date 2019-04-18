from django.contrib import admin
from django.utils.safestring import mark_safe
from reversion.admin import VersionAdmin
from urllib.parse import quote

from .models import File
from .filters import IsTabularListFilter


@admin.register(File)
class FileAdmin(VersionAdmin):
    list_display = ('title', 'file', 'mime_type',)
    readonly_fields = ('document_preview',)
    search_fields = ('title', 'file', 'mime_type', )
    list_filter = (IsTabularListFilter,)

    def document_preview(self, instance):
        return mark_safe(
            '''
            <object data="{url}" height="{height}" width="{width}">
                <img style="max-height:{height};max-width:{width}" src="{url}"/>
                <object data="{url}" height="{height}" width="{width}" type="application/pdf">
                    <iframe src="https://docs.google.com/viewer?url={url_encode}&embedded=true">
                    </iframe>
                </object>
            </object>
            '''.format(
                url=instance.file.url,
                url_encode=quote(instance.file.url),
                height='600px',
                width='800px',
            ),
        )
    document_preview.short_description = 'Document Preview'
    document_preview.allow_tags = True
