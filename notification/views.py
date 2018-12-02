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

    # Change notification to seen once requested
    def finalize_response(self, request, *args, **kwargs):
        result = super().finalize_response(request, *args, **kwargs)

        if not getattr(request, 'child_route', False):
            queryset = self.paginate_queryset(
                self.filter_queryset(self.get_queryset()))
            Notification.objects\
                .filter(id__in=[q.id for q in queryset])\
                .update(status=Notification.STATUS_SEEN)

        return result

    @list_route(
        permission_classes=[permissions.IsAuthenticated],
        url_path='unseen-count',
    )
    def get_count(self, request, version=None):
        request.child_route = True
        qs = self.filter_queryset(self.get_queryset())
        total = qs.count()

        unseen_count = qs.filter(
            status=Notification.STATUS_UNSEEN).count()

        result = {'unseen': unseen_count, 'total': total}
        return response.Response(result)
