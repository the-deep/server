from rest_framework import (
    viewsets,
    mixins,
    permissions,
    filters,
    response,
)
from rest_framework.decorators import action

import django_filters

from deep.paginations import AutocompleteSetPagination

from connector.sources.base import OrganizationSearch
from .serializers import (
    OrganizationSerializer,
    OrganizationTypeSerializer,
)
from .models import (
    Organization,
    OrganizationType,
)


class OrganizationTypeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrganizationTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = OrganizationType.objects.all()
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title', 'description',)


class OrganizationViewSet(
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.ListModelMixin,
        viewsets.GenericViewSet,
):
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = AutocompleteSetPagination
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title', 'short_name', 'long_name', 'url',)
    filterset_fields = ('verified',)
    ordering = ('title',)

    def get_queryset(self):
        if self.kwargs.get('pk'):
            return Organization.objects.select_related('parent')
        return Organization.objects.filter(parent=None)

    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        methods=['post'],
        url_path='get-or-create',
    )
    def get_or_create(self, request, version=None):
        titles = request.data.get('organizations')
        organization_search = OrganizationSearch(titles)
        return response.Response({
            'results': [
                {
                    'key': title,
                    'organization': self.get_serializer(organization_search.get(title)).data
                } for title in titles
            ]
        })
