from rest_framework import viewsets, mixins, permissions, filters

import django_filters

from deep.paginations import AutocompleteSetPagination
from deep.authentication import CSRFExemptSessionAuthentication

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
    authentication_classes = [CSRFExemptSessionAuthentication]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title', 'short_name', 'long_name', 'url',)
    filterset_fields = ('verified',)
    ordering = ('title',)

    def get_queryset(self):
        if self.kwargs.get('pk'):
            return Organization.objects.prefetch_related('parent')
        return Organization.objects.filter(parent=None)


