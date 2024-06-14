from django.contrib import admin
from reversion.admin import VersionAdmin

from deep.admin import document_preview

from .filters import IsTabularListFilter
from .models import File


@admin.register(File)
class FileAdmin(VersionAdmin):
    list_display = (
        "title",
        "file",
        "mime_type",
    )
    readonly_fields = (document_preview("file"),)
    search_fields = (
        "title",
        "file",
        "mime_type",
    )
    list_filter = (IsTabularListFilter,)
    autocomplete_fields = (
        "created_by",
        "modified_by",
        "projects",
    )
