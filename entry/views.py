from django.db import models
from rest_framework import (
    filters,
    pagination,
    permissions,
    response,
    viewsets,
)
from deep.permissions import ModifyPermission
from user_resource.filters import UserResourceFilterSet
import django_filters

from lead.models import Lead
from analysis_framework.models import Filter

from lead.serializers import SimpleLeadSerializer

from .models import (
    Entry, Attribute, FilterData, ExportData
)
from .serializers import (
    EntrySerializer, AttributeSerializer,
    FilterDataSerializer, ExportDataSerializer
)

from collections import OrderedDict


class EntryPaginationByLead(pagination.LimitOffsetPagination):
    def paginate_queryset(self, queryset, request, view=None):
        self.limit = int(request.query_params.get('limit', self.default_limit))
        if not self.limit:
            return None

        self.request = request
        self.offset = int(request.query_params.get('offset', 0))

        lead_ids = queryset.values_list('lead__id', flat=True).distinct()
        self.count = lead_ids.count()

        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []

        lead_ids = list(lead_ids[self.offset:self.offset + self.limit])
        self.leads = Lead.objects.filter(pk__in=lead_ids).distinct()

        return list(queryset.filter(lead__pk__in=lead_ids))

    def get_paginated_response(self, data):
        leads = SimpleLeadSerializer(self.leads, many=True).data
        return response.Response(OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', {
                'leads': leads,
                'entries': data,
            })
        ]))


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

    pagination_class = EntryPaginationByLead
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

            query = self.request.GET.get(filter.key)
            query_lt = self.request.GET.get(
                filter.key + '__lt'
            )
            query_gt = self.request.GET.get(
                filter.key + '__gt'
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

        return entries.order_by('-lead__created_by', 'lead')


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
