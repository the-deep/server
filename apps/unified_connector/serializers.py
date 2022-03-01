from rest_framework import serializers

from deep.serializers import TempClientIdMixin
from deep.serializers import ProjectPropertySerializerMixin
from user_resource.serializers import UserResourceSerializer

from .models import (
    UnifiedConnector,
    ConnectorSource,
)


class ConnectorSourceGqSerializer(ProjectPropertySerializerMixin, TempClientIdMixin, UserResourceSerializer):
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
    sources = ConnectorSourceGqSerializer(required=False, many=True)

    class Meta:
        model = UnifiedConnector
        fields = (
            'title',
            'is_active',
            'sources',
            'client_id',  # From TempClientIdMixin
        )

    # NOTE: This is a custom function (apps/user_resource/serializers.py::UserResourceSerializer)
    # This makes sure only scoped (individual entry) instances (attributes) are updated.
    def _get_prefetch_related_instances_qs(self, qs):
        if self.instance:
            return qs.filter(unified_connector=self.instance)
        return qs.none()  # On create throw error if existing id is provided

    def validate_sources(self, sources):
        source_found = set()
        # Only allow unique source per unified connectors
        for source in sources:
            source_type = source['source']
            if source_type in source_found:
                raise serializers.ValidationError(f'Multiple connector found for {source_type}')
            source_found.add(source_type)
        return sources

    def validate(self, data):
        data['project'] = self.project
        return data
