from django.db import models
from rest_framework import viewsets, permissions, filters
from deep.permissions import ModifyPermission
from user_resource.filters import UserResourceFilterSet
import django_filters

from lead.models import Lead
from analysis_framework.models import Filter
from .models import (
    Entry, Attribute, FilterData, ExportData
)
from .serializers import (
    EntrySerializer, AttributeSerializer,
    FilterDataSerializer, ExportDataSerializer
)


class EntryFilterSet(UserResourceFilterSet):
    """
    Entry filter set

    Basic filtering with lead, excerpt, lead title and dates
    """
    lead = django_filters.ModelMultipleChoiceFilter(
        queryset=Lead.objects.all(),
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )
    lead__published_on__lte = django_filters.DateFilter(
        name='lead__published_on', lookup_expr='lte',
    )
    lead__published_on__gte = django_filters.DateFilter(
        name='lead__published_on', lookup_expr='gte',
    )

    class Meta:
        model = Entry
        fields = ['id', 'excerpt', 'lead__title',
                  'created_at', 'created_by', 'modified_at', 'modified_by']
        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


class EntryViewSet(viewsets.ModelViewSet):
    """
    Entry view set
    """
    serializer_class = EntrySerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter)
    filter_class = EntryFilterSet
    search_fields = ('lead__title', 'excerpt')

    def get_queryset(self):
        """
        Get queryset of entries based on filters in query params
        """
        entries = Entry.get_for(self.request.user)
        filters = Filter.get_for(self.request.user)

        for filter in filters:
            # For each filter, see if there is a query for that filter
            # and then perform filtering based on that query.

            query = self.request.GET.get(filter.widget_id)
            query_lt = self.request.GET.get(
                filter.widget_id + '__lt'
            )
            query_gt = self.request.GET.get(
                filter.widget_id + '__gt'
            )

            if filter.filter_type == Filter.NUMBER:
                if query:
                    entries = entries.filter(
                        filterdata__filter=filter,
                        filterdata__number=query,
                    )
                if query_lt:
                    entries = entries.filter(
                        filterdata__filter=filter,
                        filterdata__number__lt=query_lt,
                    )
                if query_gt:
                    entries = entries.filter(
                        filterdata__filter=filter,
                        filterdata__number__gt=query_gt,
                    )

            if filter.filter_type == Filter.LIST and query:
                    query = query.split(',')

                    if len(query) > 0:
                        entries = entries.filter(
                            filterdata__filter=filter,
                            filterdata__values__contains=query,
                        )

        return entries


class AttributeViewSet(viewsets.ModelViewSet):
    serializer_class = AttributeSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return Attribute.get_for(self.request.user)


class FilterDataViewSet(viewsets.ModelViewSet):
    serializer_class = FilterDataSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return FilterData.get_for(self.request.user)


class ExportDataViewSet(viewsets.ModelViewSet):
    serializer_class = ExportDataSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return ExportData.get_for(self.request.user)
