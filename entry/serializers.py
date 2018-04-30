from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin
from user_resource.serializers import UserResourceSerializer
from analysis_framework.serializers import SimpleWidgetSerializer
from .models import (
    Entry, Attribute, FilterData, ExportData
)


class AttributeSerializer(RemoveNullFieldsMixin,
                          DynamicFieldsMixin, serializers.ModelSerializer):
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


class FilterDataSerializer(RemoveNullFieldsMixin,
                           DynamicFieldsMixin, serializers.ModelSerializer):
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


class ExportDataSerializer(RemoveNullFieldsMixin,
                           DynamicFieldsMixin, serializers.ModelSerializer):
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


class SimpleAttributeSerializer(RemoveNullFieldsMixin,
                                serializers.ModelSerializer):

    widget_obj = SimpleWidgetSerializer(source='widget',
                                        read_only=True)

    class Meta:
        model = Attribute
        fields = ('id', 'data', 'widget', 'widget_obj')


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
    """
    Entry Model Serializer
    """
    attributes = SimpleAttributeSerializer(source='attribute_set',
                                           many=True,
                                           required=False)
    # filter_data = SimpleFilterDataSerializer(source='filterdata_set',
    #                                          many=True,
    #                                          required=False)
    # export_data = SimpleExportDataSerializer(source='exportdata_set',
    #                                          many=True,
    #                                          required=False)

    class Meta:
        model = Entry
        fields = ('id', 'lead', 'analysis_framework',
                  'entry_type', 'excerpt', 'image', 'information_date',
                  'attributes', 'order',
                  'created_at', 'created_by', 'modified_at', 'modified_by',
                  'version_id')
