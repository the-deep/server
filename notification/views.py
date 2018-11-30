from django.shortcuts import render
from .serializers import (NotificationSerializer)
from .models import (Notification)

from rest_framework import (
    permissions,
    response,
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

        # TODO: implement ordering

        if project is not None:
            qs.filter(project=project)

        return qs
