import django_filters
from rest_framework.decorators import list_route

from .serializers import (
    NotificationSerializer,
    NotificationStatusSerializer
)
from .models import (Notification)

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
    filter_fields = ('project',)

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

    @list_route(permission_classes=[permissions.IsAuthenticated],
                methods=['put'],
                url_path='status')
    def status_update(self, request, version=None):
        serializer = NotificationStatusSerializer(data=request.data, many=True)
        valid = serializer.is_valid()
        if not valid:
            raise exceptions.ValidationError(serializer.errors)
        for item in serializer.data:
            notification = Notification.objects.get(id=item['id'])
            notification.status = item['status']
            notification.save()
        return response.Response()

    @list_route(
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
