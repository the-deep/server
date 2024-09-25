from django.utils import timezone
from datetime import timedelta
import django_filters
from django.db import models
from rest_framework import (
    permissions,
    response,
    status,
    filters,
    viewsets,
)
from rest_framework.decorators import action
from deep.permissions import ModifyPermission
from deep.paginations import SmallSizeSetPagination

from entry.models import Entry
from .models import (
    AnalysisFramework, Widget, Filter, Exportable,
    AnalysisFrameworkMembership,
)
from .serializers import (
    AnalysisFrameworkSerializer,
    WidgetSerializer,
    FilterSerializer, ExportableSerializer,
    AnalysisFrameworkMembershipSerializer,
)
from .filter_set import AnalysisFrameworkFilterSet
from .permissions import FrameworkMembershipModifyPermission


class AnalysisFrameworkViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisFrameworkSerializer
    permission_classes = [permissions.IsAuthenticated, ModifyPermission]
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter, filters.OrderingFilter,
    )
    filterset_class = AnalysisFrameworkFilterSet
    search_fields = ('title', 'description',)

    def get_queryset(self):
        query_params = self.request.query_params
        queryset = AnalysisFramework.get_for(self.request.user).select_related('organization')
        month_ago = timezone.now() - timedelta(days=30)
        activity_param = query_params.get('activity')

        # Active/Inactive Filter
        if activity_param in ['active', 'inactive']:
            queryset = queryset.annotate(
                recent_entry_exists=models.Exists(
                    Entry.objects.filter(
                        analysis_framework_id=models.OuterRef('id'),
                        modified_at__date__gt=month_ago,
                    )
                ),
            ).filter(
                recent_entry_exists=activity_param.lower() == 'active',
            )

        # Owner Filter
        if query_params.get('relatedToMe', 'false').lower() == 'true':
            queryset = queryset.filter(members=self.request.user)
        return queryset

    @action(
        detail=True,
        url_path='memberships',
        methods=['get'],
    )
    def get_memberships(self, request, pk=None, version=None):
        framework = self.get_object()
        memberships = AnalysisFrameworkMembership.objects.filter(framework=framework).select_related(
            'member', 'role', 'added_by'
        )
        serializer = AnalysisFrameworkMembershipSerializer(
            self.paginate_queryset(memberships),
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)


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


class AnalysisFrameworkMembershipViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisFrameworkMembershipSerializer
    permission_classes = [permissions.IsAuthenticated,
                          FrameworkMembershipModifyPermission]
    pagination_class = SmallSizeSetPagination

    def get_queryset(self):
        return AnalysisFrameworkMembership.get_for(self.request.user).select_related(
            'member', 'role', 'added_by'
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Don't let user delete him/herself
        if request.user == instance.member:
            return response.Response(
                {'message': 'You cannot remove yourself from framework'},
                status=status.HTTP_403_FORBIDDEN,
            )

        self.perform_destroy(instance)
        return response.Response(status=status.HTTP_204_NO_CONTENT)
