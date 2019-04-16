from rest_framework import viewsets, mixins, permissions, filters

import django_filters

from .serializers import OrganizationSerializer
from .models import Organization


class OrganizationViewSet(
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.ListModelMixin,
        viewsets.GenericViewSet,
):
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Organization.objects.all()
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title', 'short_name', 'long_name', 'url',)
    filterset_fields = ('verified',)
