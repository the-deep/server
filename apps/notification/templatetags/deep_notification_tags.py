from django import template
from django.conf import settings
from django.core.files.storage import FileSystemStorage, get_storage_class
from django.templatetags.static import static
from mdmail.api import EmailContent

register = template.Library()

StorageClass = get_storage_class()


@register.filter(is_safe=True)
def markdown_render(value):
    if value:
        content = EmailContent(value)
        return content.html
    return "-"


@register.filter(is_safe=True)
def static_full_path(path):
    static_path = static(path)
    if StorageClass == FileSystemStorage:
        return f"{settings.HTTP_PROTOCOL}://{settings.DJANGO_API_HOST}{static_path}"
    # With s3 storage
    return static_path
