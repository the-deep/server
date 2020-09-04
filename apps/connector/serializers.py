from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin
from organization.serializers import SimpleOrganizationSerializer
from user_resource.serializers import UserResourceSerializer
from lead.models import Lead
from lead.views import check_if_url_exists

from .sources.store import source_store
from .models import (
    Connector,
    ConnectorSource,
    ConnectorUser,
    ConnectorProject,

    UnifiedConnector,
    UnifiedConnectorSource,
    ConnectorLead,
)


class SourceOptionSerializer(RemoveNullFieldsMixin,
                             DynamicFieldsMixin,
                             serializers.Serializer):
    key = serializers.CharField()
    field_type = serializers.CharField()
    title = serializers.CharField()
    options = serializers.ListField(
        serializers.DictField(serializers.CharField)
    )


class SourceSerializer(RemoveNullFieldsMixin,
                       DynamicFieldsMixin,
                       serializers.Serializer):
    title = serializers.CharField()
    key = serializers.CharField()
    options = SourceOptionSerializer(many=True)
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        key = obj.key
        source_obj = ConnectorSource.objects.filter(key=key).first()
        # By default status is working if not added in the db
        if source_obj is None:
            return ConnectorSource.STATUS_WORKING
        return source_obj.status


class SourceEMMEntitiesSerializer(serializers.Serializer):
    name = serializers.CharField()


class SourceEMMTriggerSerializer(serializers.Serializer):
    emm_keyword = serializers.CharField()
    emm_risk_factor = serializers.CharField()
    count = serializers.IntegerField()


class SourceDataSerializer(RemoveNullFieldsMixin, serializers.ModelSerializer):
    existing = serializers.SerializerMethodField()
    key = serializers.CharField(source='id')
    emm_entities = serializers.SerializerMethodField()
    emm_triggers = serializers.SerializerMethodField()

    # M2M authors field
    authors = serializers.SerializerMethodField()
    authors_detail = serializers.SerializerMethodField()

    # TODO: Remove (Legacy)
    author_detail = SimpleOrganizationSerializer(source='author', read_only=True)

    source_detail = SimpleOrganizationSerializer(source='source', read_only=True)

    class Meta:
        model = Lead
        fields = (
            'key', 'title', 'source', 'source_type', 'url',
            'website', 'published_on', 'existing',
            'emm_entities', 'emm_triggers', 'source_detail',
            'author_detail', 'authors', 'authors_detail',
            'source_raw', 'author_raw',
        )

    def get_authors(self, lead):
        if hasattr(lead, '_authors'):
            return [author.pk for author in lead._authors]
        return []

    def get_authors_detail(self, lead):
        if hasattr(lead, '_authors'):
            return SimpleOrganizationSerializer(lead._authors, many=True).data
        return []

    def get_emm_entities(self, lead):
        if hasattr(lead, '_emm_entities'):
            return SourceEMMEntitiesSerializer(lead._emm_entities, many=True).data
        return []

    def get_emm_triggers(self, lead):
        if hasattr(lead, '_emm_triggers'):
            return SourceEMMTriggerSerializer(lead._emm_triggers, many=True).data
        return []

    def get_existing(self, lead):
        if not self.context.get('request'):
            return False

        return check_if_url_exists(lead.url,
                                   self.context['request'].user,
                                   self.context.get('project'))


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
    source = serializers.PrimaryKeyRelatedField(queryset=ConnectorSource.objects.all())
    source_title = serializers.CharField(source='source.title', read_only=True)
    role = serializers.SerializerMethodField()
    filters = serializers.SerializerMethodField()
    status = serializers.CharField(source='source.status', read_only=True)

    class Meta:
        model = Connector
        fields = ('__all__')

    def create(self, validated_data):
        connector = super().create(validated_data)
        ConnectorUser.objects.create(
            connector=connector,
            user=self.context['request'].user,
            role='admin',
        )
        return connector

    def get_role(self, connector):
        request = self.context['request']
        user = request.GET.get('user', request.user)

        usership = ConnectorUser.objects.filter(
            connector=connector,
            user=user
        ).first()
        if usership:
            return usership.role

        return None

    def get_filters(self, connector):
        source = source_store[connector.source.key]()
        if not hasattr(source, 'filters'):
            return []
        return source.filters


# ------------------------------------- UNIFIED CONNECTOR -------------------------------------- #

class ConnectorLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectorLead
        fields = '__all__'


class UnifiedConnectorSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnifiedConnectorSource
        exclude = ('leads',)


class UnifiedConnectorSerializer(UserResourceSerializer):
    sources = UnifiedConnectorSourceSerializer(source='unifiedconnectorsource_set', many=True)

    class Meta:
        model = UnifiedConnector
        fields = '__all__'
