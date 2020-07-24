import django_filters
from rest_framework.decorators import action

from .serializers import NotificationSerializer
from .models import Notification
from notification.filter_set import NotificationFilterSet

from rest_framework import (
    exceptions,
    response,
    permissions,
    viewsets,
)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_fields = ('project',)
    filterset_class = NotificationFilterSet

    def get_queryset(self):
        return Notification.get_for(
            self.request.user,
        )

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        project = self.request.query_params.get('project')

        if project is not None:
            qs.filter(project=project)

        return qs

    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        methods=['put'],
        serializer_class=NotificationSerializer,
        url_path='status',
    )
    def status_update(self, request, version=None):
        serializer = self.get_serializer(
            data=request.data, many=True, partial=True
        )
        if not serializer.is_valid():
            raise exceptions.ValidationError(serializer.errors)
        serializer.save()
        return response.Response()

    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        url_path='count',
    )
    def get_count(self, request, version=None):
        request.child_route = True
        qs = self.filter_queryset(self.get_queryset())
        total = qs.count()

        unseen_count = qs.filter(
            status=Notification.STATUS_UNSEEN).count()

        result = {'unseen': unseen_count, 'total': total}
        return response.Response(result)
