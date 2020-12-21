from deep.serializers import (
    NestedCreateMixin,
    NestedUpdateMixin,
)
from rest_framework import serializers
from reversion.models import Version
import reversion


class UserResourceSerializer(NestedCreateMixin,
                             NestedUpdateMixin,
                             serializers.ModelSerializer):

    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    modified_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.profile.get_display_name',
        read_only=True)
    modified_by_name = serializers.CharField(
        source='modified_by.profile.get_display_name',
        read_only=True)

    client_id = serializers.CharField(required=False)
    version_id = serializers.SerializerMethodField()

    def create(self, validated_data):
        client_id = validated_data.get('client_id')
        if client_id:
            ModelClass = self.Meta.model
            item = ModelClass.objects.filter(client_id=client_id).first()
            if item:
                validated_data['id'] = item.id
                return self.update(item, validated_data)

        resource = super().create(validated_data)
        resource.created_by = self.context['request'].user
        resource.modified_by = self.context['request'].user
        resource.save()
        return resource

    def update(self, instance, validated_data):
        resource = super().update(instance, validated_data)
        resource.modified_by = self.context['request'].user
        resource.save()
        return resource

    def get_version_id(self, resource):
        if not reversion.is_registered(resource.__class__):
            return None
        version_id = len(Version.objects.get_for_object(resource))

        if self.context['request'].method in ['POST', 'PUT', 'PATCH']:
            version_id += 1
        return version_id
