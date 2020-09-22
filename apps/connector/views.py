from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import (
    filters,
    exceptions,
    permissions,
    response,
    views,
    viewsets,
)
import django_filters

from rest_framework.decorators import action
from deep.paginations import HardLimitSetPagination
from deep.permissions import ModifyPermission, IsProjectMember
from project.models import Project
from utils.common import parse_number

from .filters import (
    UnifiedConnectorSourceLeadFilterSet,
    UnifiedConnectorFilterSet,
)
from .serializers import (
    SourceSerializer,
    SourceDataSerializer,

    ConnectorSerializer,
    ConnectorUserSerializer,
    ConnectorProjectSerializer,

    UnifiedConnectorSerializer,
    UnifiedConnectorSourceSerializer,
    UnifiedConnectorWithTrendingStatsSerializer,
    UnifiedConnectorSourceLeadSerializer,
)
from .models import (
    Connector,
    ConnectorUser,
    ConnectorProject,
    ConnectorSource,

    UnifiedConnector,
    UnifiedConnectorSource,
    UnifiedConnectorSourceLead,
)
from .sources.store import source_store
from .sources.base import Source
from .tasks import process_unified_connector


class SourceViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, version=None):
        sources = [s() for s in source_store.values()]
        sources_from_db = {
            source.key: source for source in ConnectorSource.objects.all()
        }
        for source in sources:
            source.db_config = sources_from_db.get(source.key)
        serializer = SourceSerializer(sources, context={'request': request}, many=True)
        results = serializer.data
        return response.Response({
            'count': len(results),
            'results': results,
        })


class SourceQueryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def query(self, source_type, query, params):
        source = source_store[source_type]()
        method = getattr(source, 'query_{}'.format(query))

        query_params = self.request.query_params

        offset = parse_number(query_params.get('offset')) or 0
        limit = parse_number(query_params.get('limit')) or Source.DEFAULT_PER_PAGE

        args = ()
        if query == 'leads':
            args = (offset, limit)

        results = method(params, *args)

        if isinstance(results, list):
            return response.Response({
                'count': len(results),
                'results': results,
                'has_emm_triggers': getattr(source, 'has_emm_triggers', False),
                'has_emm_entities': getattr(source, 'has_emm_entities', False),
            })

        return response.Response(results)

    def get(self, request, source_type, query, version=None):
        return self.query(source_type, query, request.GET)

    def post(self, request, source_type, query, version=None):
        return self.query(source_type, query, request.data)


class ConnectorViewSet(viewsets.ModelViewSet):
    serializer_class = ConnectorSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        user = self.request.GET.get('user', self.request.user)
        project_ids = self.request.GET.get('projects')
        connectors = Connector.get_for(user)

        role = self.request.GET.get('role')
        if role:
            users = ConnectorUser.objects.filter(
                role=role,
                user=user,
            )
            connectors = connectors.filter(
                connectoruser__in=users
            )

        if not project_ids:
            return connectors

        project_ids = project_ids.split(',')
        projects = ConnectorProject.objects.filter(
            project__id__in=project_ids,
        )
        self_projects = projects.filter(role='self')
        global_projects = projects.filter(role='global')

        return connectors.filter(
            models.Q(connectorproject__in=self_projects, users=user) |
            models.Q(connectorproject__in=global_projects),
        )

    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        methods=['post'],
        url_path='leads',
        serializer_class=SourceDataSerializer
    )
    def get_leads(self, request, pk=None, version=None):
        connector = self.get_object()
        if not connector.can_get(request.user):
            raise exceptions.PermissionDenied()

        project_id = request.data.pop('project', None)
        project = project_id and Project.objects.get(id=project_id)

        offset = request.data.pop('offset', None) or 0
        limit = request.data.pop('limit', None) or Source.DEFAULT_PER_PAGE

        params = {
            **(connector.params or {}),
            **(request.data or {}),
        }

        source = source_store[connector.source.key]()
        data, count = source.get_leads(params, offset=offset, limit=limit)

        # Paginate manually
        # FIXME: Make this better: probably cache, and also optimize
        # Because, right now, every data is pulled and then only paginated

        serializer = SourceDataSerializer(
            data,
            many=True,
            context={'request': request, 'project': project},
        )
        results = serializer.data

        return response.Response({
            'count': count,
            'has_emm_triggers': getattr(source, 'has_emm_triggers', False),
            'has_emm_entities': getattr(source, 'has_emm_entities', False),
            'count_per_page': limit,
            'results': results,
        })


class ConnectorUserViewSet(viewsets.ModelViewSet):
    serializer_class = ConnectorUserSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_serializer(self, *args, **kwargs):
        data = kwargs.get('data')
        list = data and data.get('list')
        if list:
            kwargs.pop('data')
            kwargs.pop('many', None)
            return super().get_serializer(
                data=list,
                many=True,
                *args,
                **kwargs,
            )
        return super().get_serializer(
            *args,
            **kwargs,
        )

    def get_queryset(self):
        return ConnectorUser.get_for(self.request.user)


class ConnectorProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ConnectorProjectSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_serializer(self, *args, **kwargs):
        data = kwargs.get('data')
        list = data and data.get('list')
        if list:
            kwargs.pop('data')
            kwargs.pop('many', None)
            return super().get_serializer(
                data=list,
                many=True,
                *args,
                **kwargs,
            )
        return super().get_serializer(
            *args,
            **kwargs,
        )

    def get_queryset(self):
        return ConnectorProject.get_for(self.request.user)


# ------------------------------------- UNIFIED CONNECTOR -------------------------------------- #

class UnifiedConnectorViewSet(viewsets.ModelViewSet):
    serializer_class = UnifiedConnectorSerializer
    permission_classes = [permissions.IsAuthenticated, ModifyPermission, IsProjectMember]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_class = UnifiedConnectorFilterSet

    def get_queryset(self):
        return UnifiedConnector.objects.filter(project_id=self.kwargs['project_id']).prefetch_related(
            models.Prefetch(
                'unifiedconnectorsource_set',
                queryset=UnifiedConnectorSource.objects.annotate(
                    total_leads=models.Count('leads', distinct=True),
                ),
            ),
        )

    def get_serializer_class(self):
        if self.request.query_params.get('with_trending_stats', 'false').lower() == 'true':
            return UnifiedConnectorWithTrendingStatsSerializer
        return super().get_serializer_class()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project'] = Project.objects.get(pk=self.kwargs['project_id'])
        return context

    @action(
        detail=True,
        url_path='trigger-sync',
        methods=('post',),
        # TODO: Better permissions
        permission_classes=[permissions.IsAuthenticated],
    )
    def trigger_sync(self, *args, **kwargs):
        unified_connector = self.get_object()
        if unified_connector.is_active:
            process_unified_connector.s(unified_connector.pk).delay()
            return response.Response({'status': 'success'})
        # TODO: Proper message structure
        return response.Response({'status': 'failed', 'message': 'inactive unified connector'})


class UnifiedConnectorSourceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UnifiedConnectorSourceSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]

    def get_queryset(self):
        return UnifiedConnectorSource.objects.filter(
            connector__project_id=self.kwargs['project_id'],
        ).annotate(total_leads=models.Count('leads', distinct=True))


class UnifiedConnectorSourceLeadViewSet(viewsets.ModelViewSet):
    pagination_class = HardLimitSetPagination
    serializer_class = UnifiedConnectorSourceLeadSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_class = UnifiedConnectorSourceLeadFilterSet
    # TODO: search_fields = ('title',)

    def get_queryset(self):
        source = get_object_or_404(
            UnifiedConnectorSource,
            pk=self.kwargs['source_id'],
            connector__project_id=self.kwargs['project_id'],
        )
        return UnifiedConnectorSourceLead.objects.filter(source=source).select_related('lead')


class UnifiedConnectorLeadViewSet(UnifiedConnectorSourceLeadViewSet):
    def get_queryset(self):
        unified_connector = get_object_or_404(
            UnifiedConnector,
            pk=self.kwargs['unified_id'],
            project_id=self.kwargs['project_id'],
        )
        return UnifiedConnectorSourceLead.objects.\
            filter(source__connector=unified_connector).select_related('lead').distinct()
