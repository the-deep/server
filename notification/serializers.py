from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin

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
                Notification.PROJECT_JOIN_REQUEST_ABORT
        ]:
            return notification.data

        return {}
