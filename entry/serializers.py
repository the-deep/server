from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer
from .models import (
    Entry, Attribute, FilterData, ExportData
)


class EntrySerializer(UserResourceSerializer):
    """
    Entry Model Serializer
    """
    class Meta:
        model = Entry
        fields = ('__all__')


class AttributeSerializer(serializers.ModelSerializer):
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


class FilterDataSerializer(serializers.ModelSerializer):
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


class ExportDataSerializer(serializers.ModelSerializer):
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
