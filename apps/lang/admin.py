from django.contrib import admin

from deep.admin import ReadOnlyMixin
from .models import (
    String,
    Link,
    LinkCollection,
)


@admin.register(String)
class StringAdmin(admin.ModelAdmin):
    search_fields = ('language', 'value',)
    list_filter = ('language',)


@admin.register(LinkCollection)
class LinkCollectionAdmin(ReadOnlyMixin, admin.ModelAdmin):
    search_fields = ('key',)


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    search_fields = ('key',)
    autocomplete_fields = ('link_collection', 'string',)
    list_display = ('key', 'string', 'language', 'link_collection')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(
            request,
            obj,
            **kwargs,
        )
        # Uncomment the following for filtering strings in admin panel
        # based on language

        # if obj:
        #     form.base_fields['string'].queryset = (
        #         form.base_fields['string'].queryset.filter(
        #             language=obj.language
        #         )
        #     )

        return form
