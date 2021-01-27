from rest_framework import serializers

from generic_relations.relations import GenericRelatedField

from deep.serializers import RemoveNullFieldsMixin
from lead.models import Lead
from lead.serializers import AssignmentLeadSerializer
from entry.models import EntryComment
from entry.serializers import AssignmentEntryCommentSerializer
from .models import (
    Notification,
    Assignment
)


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

        if notification.notification_type in Notification.TYPES:
            return notification.data

        return {}


class AssignmentSerializer(serializers.ModelSerializer):
    content_object = GenericRelatedField({
        Lead: AssignmentLeadSerializer(),
        EntryComment: AssignmentEntryCommentSerializer(),
    }, read_only=True,
    )

    class Meta:
        model = Assignment
        fields = '__all__'
        read_only_fields = ('timestamp', 'created_for', 'project', 'object_id', 'content_type')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['assignment_model_type'] = instance.content_type.model
        return data
