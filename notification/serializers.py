from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin

from .models import (Notification)


class NotificationSerializer(RemoveNullFieldsMixin,
                             serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('__all__')
