from rest_framework import viewsets, permissions
from deep.permissions import ModifyPermission

from .models import (
    Entry, Attribute, FilterData, ExportData
)
from .serializers import (
    EntrySerializer, AttributeSerializer,
    FilterDataSerializer, ExportDataSerializer
)


class EntryViewSet(viewsets.ModelViewSet):
    serializer_class = EntrySerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return Entry.get_for(self.request.user)


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
