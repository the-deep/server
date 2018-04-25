from django.contrib.auth.models import User
from django.db import models
from rest_framework import (
    filters,
    generics,
    pagination,
    permissions,
    response,
    views,
    viewsets,
)
from deep.permissions import ModifyPermission

from project.models import Project
from lead.models import Lead
from lead.serializers import SimpleLeadSerializer

from .models import (
    Attribute, FilterData, ExportData
)
from .serializers import (
    EntrySerializer, AttributeSerializer,
    FilterDataSerializer, ExportDataSerializer,
    EditEntriesDataSerializer,
)
from .filter_set import EntryFilterSet, get_filtered_entries

from collections import OrderedDict
import django_filters


class EntryPaginationByLead(pagination.LimitOffsetPagination):
    def paginate_queryset(self, queryset, request, view=None):
        self.limit = int(request.query_params.get('limit', self.default_limit))
        self.leads = None
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
        if self.leads:
            leads = SimpleLeadSerializer(self.leads, many=True).data
        else:
            leads = []
        return response.Response(OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', {
                'leads': leads,
                'entries': data,
            })
        ]))


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
        return get_filtered_entries(self.request.user, self.request.GET)


class EntryFilterView(generics.GenericAPIView):
    """
    Entry view for getting entries based filters in POST body
    """
    serializer_class = EntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = EntryPaginationByLead

    def post(self, request, version=None):
        filters = request.data.get('filters', [])
        filters = {f[0]: f[1] for f in filters}

        queryset = get_filtered_entries(request.user, filters)

        search = filters.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(lead__title__icontains=search) |
                models.Q(excerpt__icontains=search)
            )

        queryset = EntryFilterSet(filters, queryset=queryset).qs

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return response.Response(serializer.data)


class EditEntriesDataViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Page API for Edit Entries
    """
    serializer_class = EditEntriesDataSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Lead.get_for(self.request.user)


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


class EntryOptionsView(views.APIView):
    """
    Options for various attributes related to entry
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, version=None):
        project_query = request.GET.get('project')
        fields_query = request.GET.get('fields')

        projects = Project.get_for(request.user)
        if project_query:
            projects = projects.filter(id__in=project_query.split(','))

        fields = None
        if fields_query:
            fields = fields_query.split(',')

        options = {}

        def _filter_by_projects(qs, projects):
            for p in projects:
                qs = qs.filter(project=p)
            return qs

        if fields is None or 'created_by' in fields:
            created_by = _filter_by_projects(User.objects, projects)
            options['created_by'] = [
                {
                    'key': user.id,
                    'value': user.profile.get_display_name(),
                } for user in created_by.distinct()
            ]

        return response.Response(options)
