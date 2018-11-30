from django.utils.dateparse import parse_datetime
from .serializers import (NotificationSerializer)
from .models import (Notification)

from rest_framework.decorators import list_route

from rest_framework import (
    response,
    permissions,
    viewsets,
)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

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

    @list_route(
        permission_classes=[permissions.IsAuthenticated],
        url_path='unseen-count',
    )
    def get_count(self, request, version=None):
        qs = self.filter_queryset(self.get_queryset())
        total = qs.count()

        unseen_count = qs.filter(
            status=Notification.STATUS_UNSEEN).count()

        result = {'unseen': unseen_count, 'total': total}
        return response.Response(result)
