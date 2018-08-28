from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import (
    RemoveNullFieldsMixin,
    ListToDictField,
)
from user_resource.serializers import UserResourceSerializer
from lead.serializers import LeadSerializer
from lead.models import Lead
from analysis_framework.serializers import AnalysisFrameworkSerializer
from geo.serializers import GeoOptionSerializer, SimpleRegionSerializer
from .models import (
    Entry, Attribute, FilterData, ExportData
)
from project.models import Project


class AttributeSerializer(RemoveNullFieldsMixin,
                          DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ('__all__')

    # Validations
    def validate_entry(self, entry):
        if not entry.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Entry')
        return entry


class FilterDataSerializer(RemoveNullFieldsMixin,
                           DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = FilterData
        fields = ('__all__')

    # Validations
    def validate_entry(self, entry):
        if not entry.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Entry')
        return entry


class ExportDataSerializer(RemoveNullFieldsMixin,
                           DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = ExportData
        fields = ('__all__')

    # Validations
    def validate_entry(self, entry):
        if not entry.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Entry')
        return entry


class SimpleAttributeSerializer(RemoveNullFieldsMixin,
                                serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ('id', 'data', 'widget')


class SimpleFilterDataSerializer(RemoveNullFieldsMixin,
                                 serializers.ModelSerializer):
    class Meta:
        model = FilterData
        fields = ('id', 'filter', 'values', 'number')


class SimpleExportDataSerializer(RemoveNullFieldsMixin,
                                 serializers.ModelSerializer):
    class Meta:
        model = ExportData
        fields = ('id', 'exportable', 'data')


class EntrySerializer(RemoveNullFieldsMixin,
                      DynamicFieldsMixin, UserResourceSerializer):
    attributes = ListToDictField(
        child=SimpleAttributeSerializer(many=True),
        key='widget',
        source='attribute_set',
        required=False,
    )

    project = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=Project.objects.all()
    )

    class Meta:
        model = Entry
        fields = ('id', 'lead', 'analysis_framework', 'project',
                  'entry_type', 'excerpt', 'image', 'information_date',
                  'attributes', 'order', 'client_id',
                  'created_at', 'created_by', 'modified_at', 'modified_by',
                  'version_id')

    def create(self, data):
        data['project'] = data['lead'].project
        return super().create(data)


class EditEntriesDataSerializer(RemoveNullFieldsMixin,
                                serializers.ModelSerializer):
    lead = LeadSerializer(source='*', read_only=True)
    entries = EntrySerializer(source='entry_set', many=True, read_only=True)
    analysis_framework = AnalysisFrameworkSerializer(
        source='project.analysis_framework',
        read_only=True,
    )
    geo_options = serializers.SerializerMethodField()
    regions = SimpleRegionSerializer(source='project.regions', many=True,
                                     read_only=True)

    class Meta:
        model = Lead
        fields = ('lead', 'entries', 'analysis_framework', 'geo_options',
                  'regions')

    def get_geo_options(self, lead):
        # TODO Check if geo option is required based on analysis framework
        options = {}
        for region in lead.project.regions.all():
            options[str(region.id)] = GeoOptionSerializer(
                region.get_geo_areas(),
                many=True,
            ).data
        return options
