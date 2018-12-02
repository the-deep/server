from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin

from project.serializers import (
    ProjectJoinRequestSerializer,
)
from project.models import (
    ProjectJoinRequest,
)
from .models import (Notification)


class NotificationStatusSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=Notification.STATUS_CHOICES)

    def validate_id(self, id):
        if Notification.objects.filter(id=id).exists():
            return id
        else:
            raise serializers.ValidationError(
                'Non existent notification for id {}'.format(id)
            )

    def validate_status(self, status):
        if status not in dict(Notification.STATUS_CHOICES):
            raise serializers.ValidationError(
                'Invalid value for status: {}'.format(status)
            )
        return status


class NotificationSerializer(RemoveNullFieldsMixin,
                             serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ('__all__')
        read_only_fields = (
            'data', 'receiver', 'project', 'notification_type'
        )

    def get_data(self, notification):
        if not notification.data:
            return {}

        if notification.notification_type in [
                Notification.PROJECT_JOIN_REQUEST,
                Notification.PROJECT_JOIN_RESPONSE,
        ]:
            try:
                join_request = ProjectJoinRequest.objects.get(
                    id=notification.data['join_request_id']
                )
                return ProjectJoinRequestSerializer(join_request).data
            except ProjectJoinRequest.DoesNotExist:
                return {}

        elif notification.notification_type ==\
                Notification.PROJECT_JOIN_REQUEST_ABORT:
            return notification.data

        return {}
