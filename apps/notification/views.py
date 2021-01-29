import django_filters
from rest_framework.decorators import action

from .serializers import NotificationSerializer, AssignmentSerializer
from .models import Notification, Assignment
from notification.filter_set import (
    NotificationFilterSet,
    AssignmentFilterSet
)

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

        unseen_notifications = qs.filter(status=Notification.STATUS_UNSEEN)

        unseen_requests_count = unseen_notifications.filter(data__status='pending').count()
        unseen_notifications_count = unseen_notifications.count() - unseen_requests_count

        result = {
            'unseen_notifications': unseen_notifications_count,
            'unseen_requests': unseen_requests_count,
            'total': total,
        }
        return response.Response(result)


class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_class = AssignmentFilterSet

    def get_queryset(self):
        return Assignment.get_for(
            self.request.user,
        )

    @action(
        detail=False,
        methods=['POST'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='bulk-mark-as-done'
    )
    def status(self, request, version=None):
        queryset = self.filter_queryset(self.get_queryset()).filter(is_done=False)
        updated_rows_count = queryset.update(is_done=True)
        return response.Response({
            'assignment_updated': updated_rows_count,
        })
