from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers
from reversion.models import Version
import reversion

from deep.writable_nested_serializers import (
    NestedCreateMixin,
    NestedUpdateMixin,
)


class UserResourceBaseSerializer(serializers.Serializer):
    modified_at = serializers.DateTimeField(read_only=True)
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
        if 'created_by' in self.Meta.model._meta._forward_fields_map:
            validated_data['created_by'] = self.context['request'].user
        if 'modified_by' in self.Meta.model._meta._forward_fields_map:
            validated_data['modified_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'modified_by' in self.Meta.model._meta._forward_fields_map:
            validated_data['modified_by'] = self.context['request'].user
        return super().update(instance, validated_data)

    def get_version_id(self, resource):
        if not reversion.is_registered(resource.__class__):
            return None
        version_id = Version.objects.get_for_object(resource).count()

        request = self.context['request']
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not (request.method == 'POST' and self.context.get('post_is_used_for_filter', False)):
                version_id += 1
        return version_id


class UserResourceSerializer(UserResourceBaseSerializer, WritableNestedModelSerializer):
    def _get_prefetch_related_instances_qs(self, qs):
        return qs

    # https://github.com/beda-software/drf-writable-nested/blob/master/drf_writable_nested/mixins.py#L124-L135
    # This only handles M2M relations.
    def _prefetch_related_instances(self, field, related_data):
        model_class = field.Meta.model
        pk_list = self._extract_related_pks(field, related_data)

        qs = self._get_prefetch_related_instances_qs(model_class.objects)  # Modification added
        instances = {
            str(related_instance.pk): related_instance
            for related_instance in qs.filter(pk__in=pk_list)
        }

        return instances


class UserResourceCreatedMixin(serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DeprecatedUserResourceSerializer(
    UserResourceBaseSerializer,
    NestedCreateMixin,
    NestedUpdateMixin,
    serializers.ModelSerializer,
):
    pass
