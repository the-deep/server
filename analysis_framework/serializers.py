from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer
from .models import (
    AnalysisFramework, Widget, Filter, Exportable
)


class AnalysisFrameworkSerializer(UserResourceSerializer):
    """
    Analysis Framework Model Serializer
    """
    class Meta:
        model = AnalysisFramework
        fields = ('__all__')


class WidgetSerializer(serializers.ModelSerializer):
    """
    Widget Model Serializer
    """

    class Meta:
        model = Widget
        fields = ('__all__')

    # Validations
    def validate_region(self, widget):
        if not widget.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid widget')
        return widget


class FilterSerializer(serializers.ModelSerializer):
    """
    Filter data Serializer
    """

    class Meta:
        model = Filter
        fields = ('__all__')

    # Validations
    def validate_region(self, filter):
        if not filter.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Filter')
        return filter


class ExportableSerializer(serializers.ModelSerializer):
    """
    Export data Serializer
    """

    class Meta:
        model = Exportable
        fields = ('__all__')

    # Validations
    def validate_region(self, exportable):
        if not exportable.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Exportable')
        return exportable
