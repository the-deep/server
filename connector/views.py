from django.db import models
from rest_framework import (
    exceptions,
    permissions,
    response,
    views,
    viewsets,
)
import django_filters

from user_resource.filters import UserResourceFilterSet
from rest_framework.decorators import detail_route
from deep.permissions import ModifyPermission
from .serializers import (
    SourceSerializer,
    SourceDataSerializer,

    ConnectorSerializer,
    ConnectorUserSerializer,
    ConnectorProjectSerializer,
)
from .models import (
    Connector,
    ConnectorUser,
    ConnectorProject,
)
from project.models import Project
from .sources.store import source_store


class SourceViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, version=None):
        sources = source_store.values()
        serializer = SourceSerializer(sources, many=True)
        results = serializer.data
        return response.Response({
            'count': len(results),
            'results': results,
        })


class SourceQueryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, source_type, query, version=None):
        source = source_store[source_type]()
        method = getattr(source, 'query_{}'.format(query))
        results = method(request.GET)

        if isinstance(results, list):
            return response.Response({
                'count': len(results),
                'results': results,
            })

        return response.Response(results)


class ConnectorFilterSet(UserResourceFilterSet):
    projects = django_filters.ModelMultipleChoiceFilter(
        queryset=Project.objects.all(),
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )

    class Meta:
        model = Connector
        fields = ['id', 'title', 'source']

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


class ConnectorViewSet(viewsets.ModelViewSet):
    serializer_class = ConnectorSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_class = ConnectorFilterSet

    def get_queryset(self):
        user = self.request.GET.get('user', self.request.user)
        return Connector.get_for(user)

    @detail_route(permission_classes=[permissions.IsAuthenticated],
                  url_path='leads',
                  serializer_class=SourceDataSerializer)
    def get_leads(self, request, pk=None, version=None):
        connector = self.get_object()
        if not connector.can_get(request.user):
            raise exceptions.PermissionDenied()

        source = source_store[connector.source]()
        data = source.fetch(connector.params)
        serializer = SourceDataSerializer(
            data,
            many=True,
            context={'request': request},
        )
        results = serializer.data
        return response.Response({
            'count': len(results),
            'results': results
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
            return super(ConnectorUserViewSet, self).get_serializer(
                data=list,
                many=True,
                *args,
                **kwargs,
            )
        return super(ConnectorUserViewSet, self).get_serializer(
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
            return super(ConnectorProjectViewSet, self).get_serializer(
                data=list,
                many=True,
                *args,
                **kwargs,
            )
        return super(ConnectorProjectViewSet, self).get_serializer(
            *args,
            **kwargs,
        )

    def get_queryset(self):
        return ConnectorProject.get_for(self.request.user)
