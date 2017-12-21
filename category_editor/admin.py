from django.contrib import admin
from reversion.admin import VersionAdmin
from category_editor.models import CategoryEditor


@admin.register(CategoryEditor)
class CategoryEditorAdmin(VersionAdmin):
    pass
