import logging
from rest_framework import serializers
from django.db import transaction

from deep.serializers import (
    TempClientIdMixin,
    ProjectPropertySerializerMixin,
    IntegerIDField,
)
from user_resource.serializers import UserResourceSerializer

from .models import (
    UnifiedConnector,
    ConnectorSource,
    ConnectorSourceLead,
)
from .tasks import process_unified_connector

logger = logging.getLogger(__name__)


# ------------------- Graphql Serializers ------------------------------------
class ConnectorSourceGqSerializer(ProjectPropertySerializerMixin, TempClientIdMixin, UserResourceSerializer):
    id = IntegerIDField(required=False)
    project_property_attribute = 'unified_connector'

    class Meta:
        model = ConnectorSource
        fields = (
            'id',
            'title',
            'source',
            'params',
            'client_id',  # From TempClientIdMixin
        )




class UnifiedConnectorGqSerializer(ProjectPropertySerializerMixin, TempClientIdMixin, UserResourceSerializer):
    class Meta:
        model = UnifiedConnector
        fields = (
            'title',
            'is_active',
            'client_id',  # From TempClientIdMixin
        )

    def validate(self, data):
        data['project'] = self.project
        return data

    def create(self, data):
        instance = super().create(data)
        transaction.on_commit(
            lambda: process_unified_connector.delay(instance.pk)
        )
        return instance




class UnifiedConnectorWithSourceGqSerializer(UnifiedConnectorGqSerializer):
    sources = ConnectorSourceGqSerializer(required=False, many=True)

    class Meta:
        model = UnifiedConnector
        fields = [
            *UnifiedConnectorGqSerializer.Meta.fields,
            'sources',
        ]

    # NOTE: This is a custom function (apps/user_resource/serializers.py::UserResourceSerializer)
    # This makes sure only scoped (individual entry) instances (attributes) are updated.
    def _get_prefetch_related_instances_qs(self, qs):
        if self.instance:
            return qs.filter(unified_connector=self.instance)
        return qs.none()

    def validate_sources(self, sources):
        source_found = set()
        for source in sources:
            source_type = source['source']
            if source_type in source_found:
                raise serializers.ValidationError(f'Multiple connector found for {source_type}')
            source_found.add(source_type)
        return sources



class ConnectorSourceLeadGqSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectorSourceLead
        fields = (
            'blocked',
        )
