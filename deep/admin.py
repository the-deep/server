from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.contrib.postgres import fields
from django.contrib import admin
from urllib.parse import quote
from reversion.admin import VersionAdmin as _VersionAdmin

from jsoneditor.forms import JSONEditor


class JSONFieldMixin():
    formfield_overrides = {
        fields.JSONField: {'widget': JSONEditor},
    }


class ModelAdmin(JSONFieldMixin, admin.ModelAdmin):
    pass


class StackedInline(JSONFieldMixin, admin.StackedInline):
    pass


class VersionAdmin(JSONFieldMixin, _VersionAdmin):
    pass


def linkify(field_name):
    """
    Converts a foreign key value into clickable links.

    If field_name is 'parent', link text will be str(obj.parent)
    Link will be admin url for the admin url for obj.parent.id:change
    """
    def _linkify(obj):
        app_label = obj._meta.app_label
        linked_obj = getattr(obj, field_name)
        if linked_obj:
            model_name = linked_obj._meta.model_name
            view_name = f"admin:{app_label}_{model_name}_change"
            link_url = reverse(view_name, args=[linked_obj.pk])
            return format_html('<a href="{}">{}</a>', link_url, linked_obj)
        return '-'

    _linkify.short_description = field_name
    return _linkify


def document_preview(field_name):
    """
    Show document preview for file fields
    """
    def _document_preview(obj):
        file = getattr(obj, field_name)
        if file:
            try:
                if file.name.split('?')[0].split('.')[-1] in ['docx', 'xlsx', 'pptx', 'ods', 'doc']:
                    return mark_safe(
                        '''
                        <iframe src="https://docs.google.com/viewer?url={url_encode}&embedded=true"></iframe>
                        '''.format(url_encode=quote(file.url))
                    )
            except Exception:
                pass
            return mark_safe(
                '''
                <object data="{url}" height="{height}" width="{width}">
                    <img style="max-height:{height};max-width:{width}" src="{url}"/>
                    <iframe src="https://docs.google.com/viewer?url={url_encode}&embedded=true"></iframe>
                    </object>
                </object>
                '''.format(
                    url=file.url,
                    url_encode=quote(file.url),
                    height='600px',
                    width='800px',
                ),
            )
        return 'N/A'
    _document_preview.short_description = 'Document Preview'
    _document_preview.allow_tags = True
    return _document_preview
