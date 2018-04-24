from rest_framework import (
    viewsets,
    response,
    permissions,
)
from deep.permissions import ModifyPermission
from .serializers import (
    SourceSerializer,

    ConnectorSerializer,
    ConnectorUserSerializer,
    ConnectorProjectSerializer,
)
from .models import (
    Connector,
    ConnectorUser,
    ConnectorProject,
)
from .sources.store import source_store


class SourceViewSet(viewsets.ViewSet):
    def list(self, request, version=None):
        sources = source_store.values()
        serializer = SourceSerializer(sources, many=True)
        return response.Response({
            'count': len(serializer.data),
            'results': serializer.data,
        })


# TODO Fetch from source API that returns SourceData


class ConnectorViewSet(viewsets.ModelViewSet):
    serializer_class = ConnectorSerializer
    permissions = [permissions.IsAuthenticated,
                   ModifyPermission]

    def get_queryset(self):
        user = self.request.GET.get('user', self.request.user)
        return Connector.get_for(user)


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
