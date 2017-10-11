from rest_framework import viewsets, permissions
from deep.permissions import ModifyPermission

from .models import (
    AnalysisFramework, Widget, Filter, Exportable
)
from .serializers import (
    AnalysisFrameworkSerializer, WidgetSerializer,
    FilterSerializer, ExportableSerializer
)


class AnalysisFrameworkViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisFrameworkSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return AnalysisFramework.get_for(self.request.user)


class WidgetViewSet(viewsets.ModelViewSet):
    serializer_class = WidgetSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return Widget.get_for(self.request.user)


class FilterViewSet(viewsets.ModelViewSet):
    serializer_class = FilterSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return Filter.get_for(self.request.user)


class ExportableViewSet(viewsets.ModelViewSet):
    serializer_class = ExportableSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return Exportable.get_for(self.request.user)
