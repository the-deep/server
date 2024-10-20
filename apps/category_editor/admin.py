from django.contrib import admin
from reversion.admin import VersionAdmin
from category_editor.models import CategoryEditor


@admin.register(CategoryEditor)
class CategoryEditorAdmin(VersionAdmin):
    search_fields = ('title',)
    autocomplete_fields = ('created_by', 'modified_by',)
