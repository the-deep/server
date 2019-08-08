from django.contrib import admin
from django.contrib import messages

from deep.admin import VersionAdmin

from .models import Book, Sheet, Field, Geodata
from .filters import CacheStatusListFilter
from .tasks import tabular_generate_columns_image


class SheetInline(admin.StackedInline):
    model = Sheet


class FieldInline(admin.StackedInline):
    model = Field


class GeodataInline(admin.StackedInline):
    model = Geodata


@admin.register(Book)
class BookAdmin(VersionAdmin):
    search_fields = ('title',)
    inlines = [SheetInline]
    autocomplete_fields = ('project', 'created_by', 'modified_by', 'file',)


@admin.register(Sheet)
class SheetAdmin(VersionAdmin):
    search_fields = ('title',)
    inlines = [FieldInline]
    autocomplete_fields = ('book',)


def trigger_cache_reset(modeladmin, request, queryset):
    messages.add_message(
        request, messages.INFO,
        'Successfully triggerd fields: ' + ', '.join(
            '{}({})'.format(value[0], value[1])
            for value in queryset.values_list('title', 'id').distinct()
        )
    )
    tabular_generate_columns_image.delay(
        list(queryset.values_list('id', flat=True).distinct())
    )


trigger_cache_reset.short_description = 'Trigger cache reset for selected Fields'


@admin.register(Field)
class FieldAdmin(VersionAdmin):
    inlines = [GeodataInline]
    list_display = ('pk', 'title', 'sheet', 'type',)
    list_filter = ('type', CacheStatusListFilter)
    search_fields = ['title']
    actions = [trigger_cache_reset]
    autocomplete_fields = ('sheet',)
