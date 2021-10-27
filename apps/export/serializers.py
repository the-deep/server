from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin, ProjectPropertySerializerMixin
from .models import Export


class ExportSerializer(RemoveNullFieldsMixin, DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Serializer for export
    """

    class Meta:
        model = Export
        exclude = ('filters',)


# ------------------- Graphql Serializers ----------------------------------------
class ExportCreateGqlSerializer(ProjectPropertySerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Export
        fields = (
            'type',
            'format',
            'export_type',
            'is_preview',
            'filters',
        )

    def update(self, _):
        raise serializers.ValidationError('Update isn\'t allowed for Export')

    def create(self, data):
        data['title'] = 'Generating Export.....'
        data['exported_by'] = self.context['request'].user
        data['project'] = self.project
        return super().create(data)
