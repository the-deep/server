from rest_framework import serializers

from generic_relations.relations import GenericRelatedField

from deep.serializers import RemoveNullFieldsMixin
from user.serializers import SimpleUserSerializer
from project.serializers import SimpleProjectSerializer

from lead.models import Lead
from entry.models import EntryComment
from .models import (
    Notification,
    Assignment
)


class NotificationSerializer(RemoveNullFieldsMixin, serializers.ModelSerializer):
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
        return notification.data


class AssignmentEntryCommentSerializer(RemoveNullFieldsMixin, serializers.ModelSerializer):
    entry_excerpt = serializers.CharField(source='entry.excerpt', read_only=True)

    class Meta:
        model = EntryComment
        fields = ('id', 'text', 'entry', 'entry_excerpt',)


class AssignmentLeadSerializer(RemoveNullFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ('id', 'title',)


class AssignmentSerializer(serializers.ModelSerializer):
    content_object_details = GenericRelatedField({
        Lead: AssignmentLeadSerializer(),
        EntryComment: AssignmentEntryCommentSerializer(),
    }, read_only=True, source='content_object')
    project_details = SimpleProjectSerializer(source='project', read_only=True)
    created_by_details = SimpleUserSerializer(source='created_by', read_only=True)

    class Meta:
        model = Assignment
        read_only_fields = [
            'id',
            'created_at',
            'project_details', 'created_by_details', 'content_object_details', 'content_type'
        ]
        fields = read_only_fields + ['is_done']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['content_object_type'] = instance.content_type.model
        return data


# Graphql Serializer
class NotificationGqSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)

    class Meta:
        model = Notification
        fields = ('id', 'status')

    def update(self, instance, validated_data):
        if instance and not Notification.objects.filter(id=instance.id, receiver=self.context['request'].user).exists():
            raise serializers.ValidationError('Cannot update this notification')
        return super().update(instance, validated_data)
