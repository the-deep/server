from django.contrib.auth.models import User
from django.db import models
from rest_framework.decorators import action
from rest_framework import (
    filters,
    generics,
    permissions,
    response,
    views,
    viewsets,
)
from deep.permissions import ModifyPermission

from project.models import Project
from lead.models import Lead

from .models import (
    Entry, Attribute, FilterData, ExportData,
)
from .serializers import (
    ComprehensiveEntriesSerializer,
    EntrySerializer,
    EntryRetriveSerializer,
    EntryProccesedSerializer,
    EntryRetriveProccesedSerializer,
    AttributeSerializer,
    FilterDataSerializer,
    ExportDataSerializer,
    EditEntriesDataSerializer,
)
from .pagination import ComprehensiveEntriesSetPagination
from .filter_set import EntryFilterSet, get_filtered_entries
from tabular.models import Field as TabularField
import django_filters


class EntryViewSet(viewsets.ModelViewSet):
    """
    Entry view set
    """
    serializer_class = EntrySerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter)
    filterset_class = EntryFilterSet

    search_fields = ('lead__title', 'excerpt')

    def get_queryset(self):
        return get_filtered_entries(self.request.user, self.request.GET)

    def get_serializer_class(self):
        if self.action == 'list':
            return EntryRetriveSerializer
        return super().get_serializer_class()

    @action(
        detail=True,
        url_path='processed',
        serializer_class=EntryProccesedSerializer,
    )
    def get_proccessed_entries(self, request, version=None):
        queryset = self.filter_queryset(self.get_queryset())
        self.page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(self.page, many=True)
        return self.get_paginated_response(serializer.data)


class EntryFilterView(generics.GenericAPIView):
    """
    Entry view for getting entries based filters in POST body
    """
    serializer_class = EntryRetriveProccesedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, version=None):
        filters = request.data.get('filters', [])
        filters = {f[0]: f[1] for f in filters}

        queryset = get_filtered_entries(request.user, filters)

        project = filters.get('project')
        search = filters.get('search')

        if search:
            # For searching tabular columns
            field_filters = {}
            if project:
                field_filters['sheet__book__project'] = project

            fields = TabularField.objects.filter(
                title__icontains=search,
                **field_filters
            )
            queryset = queryset.filter(
                models.Q(lead__title__icontains=search) |
                models.Q(excerpt__icontains=search) |
                (
                    models.Q(
                        tabular_field__in=models.Subquery(
                            fields.values_list('pk', flat=True))
                    )
                )
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

        projects = Project.get_for_member(request.user)
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


class ComprehensiveEntriesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Comprehensive API for Entries
    """
    serializer_class = ComprehensiveEntriesSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ComprehensiveEntriesSetPagination

    def get_queryset(self):
        prefetch_related_fields = [
            'attribute_set', 'attribute_set__widget',
            'created_by', 'created_by__profile',
            'modified_by', 'modified_by__profile',
        ]
        return Entry.get_for(self.request.user).prefetch_related(*prefetch_related_fields)
