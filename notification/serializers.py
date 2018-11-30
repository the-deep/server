from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin

from project.serializers import (
    ProjectJoinRequest,
    ProjectJoinRequestSerializer,
)
from .models import (Notification)


class NotificationSerializer(RemoveNullFieldsMixin,
                             serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ('__all__')

    def get_data(self, notification):
        if not notification.data:
            return {}

        if notification.notification_type in [
                Notification.PROJECT_JOIN_REQUEST,
                Notification.PROJECT_JOIN_RESPONSE,
        ]:
            join_request = ProjectJoinRequest.objects.get(
                id=notification.data['join_request_id']
            )
            return ProjectJoinRequestSerializer(join_request).data
        return {}
