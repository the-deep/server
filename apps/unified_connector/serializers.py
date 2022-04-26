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
    ConnectorLead,
    ConnectorSource,
    ConnectorSourceLead,
)
from .tasks import UnifiedConnectorTask, process_unified_connector

logger = logging.getLogger(__name__)


class ExtractCallbackSerializer(serializers.Serializer):
    """
    Serialize deepl extractor
    """
    client_id = serializers.CharField()
    url = serializers.CharField()
    extraction_status = serializers.IntegerField()  # 0 = Failed, 1 = Success
    # Data fields
    images_path = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        required=False, default=[],
    )
    text_path = serializers.CharField(required=False)
    total_words_count = serializers.IntegerField(required=False, default=0)
    total_pages = serializers.IntegerField(required=False, default=0)

    def validate(self, data):
        client_id = data['client_id']
        try:
            data['lead'] = UnifiedConnectorTask.get_connector_lead_from_client_id(client_id)
            assert data['lead'].url == data['url']
        except Exception as e:
            raise serializers.ValidationError({
                'client_id': str(e)
            })
        if data['extraction_status'] == 1:
            errors = {}
            for key in ['text_path', 'total_words_count', 'total_pages']:
                if key not in data:
                    errors[key] = f'<{key}> is missing. Required when the extraction is 1 (Success)'
            if errors:
                raise serializers.ValidationError(errors)
        return data

    def create(self, data):
        success = data['extraction_status'] == 1
        connector_lead = data['lead']   # Added from validate
        if success:
            return UnifiedConnectorTask.save_connector_lead_data_from_extractor(
                connector_lead,
                data['text_path'],
                data.get('images_path', [])[:10],  # TODO: Support for more images, to much image will error.
                data['total_words_count'],
                data['total_pages'],
            )
        connector_lead.update_extraction_status(ConnectorLead.ExtractionStatus.FAILED)
        return connector_lead


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


class ConnectorSourceLeadGqSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectorSourceLead
        fields = (
            'blocked',
        )
