from django.db import models
from rest_framework import viewsets, permissions, filters
from deep.permissions import ModifyPermission
from user_resource.filters import UserResourceFilterSet
import django_filters

from lead.models import Lead
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
    lead__published_on = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Entry
        fields = ['id', 'lead', 'excerpt', 'lead__title', 'lead__published_on',
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
    serializer_class = EntrySerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter)
    filter_class = EntryFilterSet
    search_fields = ('lead__title', 'excerpt')

    def get_queryset(self):
        entries = Entry.get_for(self.request.user)
        # filter_data = FilterData.get_for(self.request.user)
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
