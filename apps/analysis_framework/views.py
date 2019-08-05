from django.utils import timezone
from datetime import timedelta
import django_filters
from django.db import models
from rest_framework import (
    exceptions,
    permissions,
    response,
    status,
    filters,
    views,
    viewsets,
)
from rest_framework.decorators import action
from deep.permissions import ModifyPermission

from project.models import Project
from entry.models import Entry
from .models import (
    AnalysisFramework, Widget, Filter, Exportable,
    AnalysisFrameworkMembership,
    AnalysisFrameworkRole,
)
from .serializers import (
    AnalysisFrameworkSerializer, WidgetSerializer,
    FilterSerializer, ExportableSerializer,
    AnalysisFrameworkMembershipSerializer,
    AnalysisFrameworkRoleSerializer,
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
        queryset = AnalysisFramework.get_for(self.request.user)
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
        memberships = AnalysisFrameworkMembership.objects.filter(framework=framework)

        serializer = AnalysisFrameworkMembershipSerializer(
            memberships,
            context={'request': request},
            many=True
        )
        return response.Response({'results': serializer.data})


class AnalysisFrameworkCloneView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, af_id, version=None):
        if not AnalysisFramework.objects.filter(
            id=af_id
        ).exists():
            raise exceptions.NotFound()

        analysis_framework = AnalysisFramework.objects.get(
            id=af_id
        )
        if not analysis_framework.can_clone(request.user):
            raise exceptions.PermissionDenied()

        cloned_title = request.data.get('title')
        if not cloned_title:
            raise exceptions.ValidationError({
                'title': 'Title should be present',
            })

        new_af = analysis_framework.clone(
            request.user,
            request.data or {},
        )
        # Set the requesting user as owner member, don't create other memberships of old framework
        new_af.add_member(request.user, new_af.get_or_create_owner_role())

        serializer = AnalysisFrameworkSerializer(
            new_af,
            context={'request': request},
        )

        project = request.data.get('project')
        if project:
            project = Project.objects.get(id=project)
            if not project.can_modify(request.user):
                raise exceptions.ValidationError({
                    'project': 'Invalid project',
                })
            project.analysis_framework = new_af
            project.modified_by = request.user
            project.save()

        return response.Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


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

    def get_queryset(self):
        return AnalysisFrameworkMembership.get_for(self.request.user)

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


class PrivateAnalysisFrameworkRoleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AnalysisFrameworkRoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AnalysisFrameworkRole.objects.filter(is_private_role=True)


class PublicAnalysisFrameworkRoleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AnalysisFrameworkRoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        no_default_role = self.request.query_params.get('is_default_role', 'true') == 'false'
        extra = {} if not no_default_role else {'is_default_role': False}

        return AnalysisFrameworkRole.objects.filter(
            is_private_role=False,
            **extra,
        )
