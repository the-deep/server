from django.contrib import admin

from deep.admin import VersionAdmin

from .models import Book, Sheet, Field, Geodata


class SheetInline(admin.StackedInline):
    model = Sheet


class FieldInline(admin.StackedInline):
    model = Field


class GeodataInline(admin.StackedInline):
    model = Geodata


@admin.register(Book)
class BookAdmin(VersionAdmin):
    inlines = [SheetInline]


@admin.register(Sheet)
class SheetAdmin(VersionAdmin):
    inlines = [FieldInline]


@admin.register(Field)
class FieldAdmin(VersionAdmin):
    inlines = [GeodataInline]
    list_display = ('title', 'sheet', 'type',)
    list_filter = ('type',)
