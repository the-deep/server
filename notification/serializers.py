from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin

from .models import (Notification)


class NotificationSerializer(RemoveNullFieldsMixin,
                             serializers.ModelSerializer):
    id = serializers.IntegerField()
    data = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ('__all__')
        read_only_fields = (
            'data', 'receiver', 'project', 'notification_type'
        )

    def create(self, validated_data):
        id = validated_data.get('id')
        if id:
            try:
                notification = Notification.objects.get(id=id)
            except Notification.DoesNotExist:
                raise serializers.ValidationError({
                    'id': 'Invalid notification id: {}'.format(id)
                })
            return self.update(notification, validated_data)
        return super().create(validated_data)

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
