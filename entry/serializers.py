from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer
from .models import (
    Entry, Attribute, FilterData, ExportData
)


class AttributeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Entry Attribute Model Serializer
    """

    class Meta:
        model = Attribute
        fields = ('__all__')

    # Validations
    def validate_entry(self, entry):
        if not entry.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Entry')
        return entry


class FilterDataSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Filter data Serializer
    """

    class Meta:
        model = FilterData
        fields = ('__all__')

    # Validations
    def validate_entry(self, entry):
        if not entry.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Entry')
        return entry


class ExportDataSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Export data Serializer
    """

    class Meta:
        model = ExportData
        fields = ('__all__')

    # Validations
    def validate_entry(self, entry):
        if not entry.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Entry')
        return entry


class SimpleAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ('id', 'data', 'widget')


class SimpleFilterDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilterData
        fields = ('id', 'filter', 'values', 'number')


class SimpleExportDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportData
        fields = ('id', 'exportable', 'data')


class EntrySerializer(DynamicFieldsMixin, UserResourceSerializer):
    """
    Entry Model Serializer
    """
    attributes = SimpleAttributeSerializer(source='attribute_set',
                                           many=True,
                                           required=False)
    filter_data = SimpleFilterDataSerializer(source='filterdata_set',
                                             many=True,
                                             required=False)
    export_data = SimpleExportDataSerializer(source='exportdata_set',
                                             many=True,
                                             required=False)

    class Meta:
        model = Entry
        fields = ('id', 'lead', 'analysis_framework', 'excerpt', 'image',
                  'attributes', 'filter_data', 'export_data',
                  'created_at', 'created_by', 'modified_at', 'modified_by',
                  'version_id')
