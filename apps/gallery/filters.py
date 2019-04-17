from django.contrib import admin
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class IsTabularListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Is Tabular Image')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'is_tabular_image'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Yes')),
            ('no', _('No')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(metadata__tabular=True)
        elif self.value() == 'no':
            return queryset.filter(~Q(metadata__tabular=True))
        else:
            return queryset.all()
