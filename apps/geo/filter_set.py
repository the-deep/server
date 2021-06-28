import django_filters

from geo.models import GeoArea

class GeoAreaFilterSet(django_filters.rest_framework.FilterSet):
    label = django_filters.CharFilter(
        label='Geo Area Label',
        method='geo_area_label'
    )

    class Meat:
        model = GeoArea
        fields = ()

    def geo_area_label(self, queryset, name, value):
        if value:
            return queryset.filter(label__icontains=value)
        return queryset
