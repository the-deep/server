from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Field


class CacheStatusListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Cache Status')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'is_cache_status'

    def lookups(self, request, model_admin):
        return Field.CACHE_STATUS_TYPES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(cache__status=self.value())
        else:
            return queryset.all()
