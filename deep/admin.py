from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.contrib.postgres import fields
from django.contrib import admin
from django.conf import settings
from urllib.parse import quote
from reversion.admin import VersionAdmin as _VersionAdmin

from jsoneditor.forms import JSONEditor as _JSONEditor


site = admin.site


def get_site_string(title):
    return f'{title} ({settings.DEEP_ENVIRONMENT.title()})'


# Text to put at the end of each page's <title>.
site.site_title = get_site_string('DEEP site admin')
# Text to put in each page's <h1> (and above login form).
site.site_header = get_site_string('DEEP Administration')
# Text to put at the top of the admin index page.
site.index_title = get_site_string('DEEP Administration')


class JSONEditor(_JSONEditor):
    class Media:
        js = [
            # NOTE: Not using this breaks autocomplete
            'admin/js/vendor/jquery/jquery%s.js' % ('' if settings.DEBUG else '.min')
        ] + list(_JSONEditor.Media.js[1:])
        css = _JSONEditor.Media.css


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


def linkify(field_name, field_field=None):
    """
    Converts a foreign key value into clickable links.

    If field_name is 'parent', link text will be str(obj.parent)
    Link will be admin url for the admin url for obj.parent.id:change
    """

    def _linkify(obj):
        linked_obj = obj
        for _field_name in field_name.split('.'):
            linked_obj = getattr(linked_obj, _field_name, None)
        if linked_obj:
            app_label = linked_obj._meta.app_label
            model_name = linked_obj._meta.model_name
            view_name = f"admin:{app_label}_{model_name}_change"
            link_url = reverse(view_name, args=[linked_obj.pk])
            return format_html(f'<a href="{link_url}">{linked_obj}</a>')

        return '-'

    _linkify.short_description = ' '.join(field_name.split('.'))
    _linkify.admin_order_field = '__'.join(field_name.split('.'))
    return _linkify


def query_buttons(description, queries):
    """
    Converts a foreign key value into clickable links.

    If field_name is 'parent', link text will be str(obj.parent)
    Link will be admin url for the admin url for obj.parent.id:change
    """
    def _query_buttons(obj):
        app_label = obj._meta.app_label
        model_name = obj._meta.model_name
        view_name = f'admin:{app_label}_{model_name}_change'
        buttons = []
        for query in queries:
            link_url = f'{reverse(view_name, args=[obj.pk])}?show_{query}=true'
            buttons.append(f'<a class="changelink" href="{link_url}">{query.title()}</a>')
        return mark_safe(''.join(buttons))

    _query_buttons.short_description = description
    return _query_buttons


def document_preview(field_name, label=None):
    """
    Show document preview for file fields
    """
    def _document_preview(obj):
        file = getattr(obj, field_name)
        if file:
            try:
                if file.name.split('?')[0].split('.')[-1] in ['docx', 'xlsx', 'pptx', 'ods', 'doc']:
                    return mark_safe(
                        f'''
                        <iframe src="https://docs.google.com/viewer?url={quote(file.url)}&embedded=true"></iframe>
                        '''
                    )
            except Exception:
                pass
            height = '600px'
            width = '800px'
            return mark_safe(f"""
                <object data="{file.url}" height="{height}" width="{width}">
                    <img style="max-height:{height};max-width:{width}" src="{file.url}"/>
                    <iframe src="https://docs.google.com/viewer?url={quote(file.url)}&embedded=true"></iframe>
                    </object>
                </object>
            """)
        return 'N/A'
    _document_preview.short_description = label or 'Document Preview'
    _document_preview.allow_tags = True
    return _document_preview
