from django.contrib import admin
from reversion.admin import VersionAdmin
from .models import Book, Sheet, Field


class SheetInline(admin.StackedInline):
    model = Sheet


class FieldInline(admin.StackedInline):
    model = Field


@admin.register(Book)
class BookAdmin(VersionAdmin):
    inlines = [SheetInline]


@admin.register(Sheet)
class SheetAdmin(VersionAdmin):
    inlines = [FieldInline]
