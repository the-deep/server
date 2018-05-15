from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin
from user_resource.serializers import UserResourceSerializer
from lead.models import Lead
from .models import (
    Connector,
    ConnectorUser,
    ConnectorProject,
)


class SourceOptionSerializer(RemoveNullFieldsMixin,
                             DynamicFieldsMixin,
                             serializers.Serializer):
    key = serializers.CharField()
    field_type = serializers.CharField()
    title = serializers.CharField()


class SourceSerializer(RemoveNullFieldsMixin,
                       DynamicFieldsMixin,
                       serializers.Serializer):
    title = serializers.CharField()
    key = serializers.CharField()
    options = SourceOptionSerializer(many=True)


class SourceDataSerializer(RemoveNullFieldsMixin,
                           serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ('title', 'source', 'source_type', 'url',
                  'website', 'published_on')


class ConnectorUserSerializer(RemoveNullFieldsMixin,
                              DynamicFieldsMixin,
                              serializers.ModelSerializer):
    email = serializers.CharField(source='user.email', read_only=True)
    display_name = serializers.CharField(
        source='user.profile.get_display_name',
        read_only=True,
    )

    class Meta:
        model = ConnectorUser
        fields = ('id', 'user', 'display_name', 'email',
                  'connector', 'role', 'added_at')

    def get_unique_together_validators(self):
        return []

    # Validations
    def validate_connector(self, connector):
        if not connector.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid connector')
        return connector


class ConnectorProjectSerializer(RemoveNullFieldsMixin,
                                 DynamicFieldsMixin,
                                 serializers.ModelSerializer):
    title = serializers.CharField(source='project.title',
                                  read_only=True)

    class Meta:
        model = ConnectorProject
        fields = ('id', 'project', 'title',
                  'connector', 'role', 'added_at')

    def get_unique_together_validators(self):
        return []

    # Validations
    def validate_connector(self, connector):
        if not connector.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid connector')
        return connector


class ConnectorSerializer(RemoveNullFieldsMixin,
                          DynamicFieldsMixin, UserResourceSerializer):
    users = ConnectorUserSerializer(
        source='connectoruser_set',
        many=True,
        required=False,
    )
    projects = ConnectorProjectSerializer(
        source='connectorproject_set',
        many=True,
        required=False,
    )

    class Meta:
        model = Connector
        fields = ('__all__')

    def create(self, validated_data):
        connector = super(ConnectorSerializer, self).create(validated_data)
        ConnectorUser.objects.create(
            connector=connector,
            user=self.context['request'].user,
            role='admin',
        )
        return connector
