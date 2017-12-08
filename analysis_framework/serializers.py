from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer

from analysis_framework.models import (
    AnalysisFramework, Widget, Filter, Exportable
)
from project.models import Project


class WidgetSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Widget Model Serializer
    """

    class Meta:
        model = Widget
        fields = ('__all__')

    # Validations
    def validate_analysis_framework(self, analysis_framework):
        if not analysis_framework.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Analysis Framework')
        return analysis_framework


class FilterSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Filter data Serializer
    """

    class Meta:
        model = Filter
        fields = ('__all__')

    # Validations
    def validate_analysis_framework(self, analysis_framework):
        if not analysis_framework.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Analysis Framework')
        return analysis_framework


class ExportableSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Export data Serializer
    """

    class Meta:
        model = Exportable
        fields = ('__all__')

    # Validations
    def validate_analysis_framework(self, analysis_framework):
        if not analysis_framework.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Analysis Framework')
        return analysis_framework


class AnalysisFrameworkSerializer(DynamicFieldsMixin, UserResourceSerializer):
    """
    Analysis Framework Model Serializer
    """
    widgets = WidgetSerializer(source='widget_set', many=True,
                               required=False)
    filters = FilterSerializer(source='filter_set', many=True,
                               required=False)
    exportables = ExportableSerializer(source='exportable_set', many=True,
                                       required=False)

    is_admin = serializers.SerializerMethodField()

    project = serializers.IntegerField(
        write_only=True,
        required=False,
    )

    class Meta:
        model = AnalysisFramework
        fields = ('id', 'title',
                  'widgets', 'filters', 'exportables',
                  'created_at', 'created_by', 'modified_at', 'modified_by',
                  'project', 'is_admin',
                  'version_id')

    def validate_project(self, project):
        try:
            project = Project.objects.get(id=project)
        except Project.DoesNotExist:
            raise serializers.ValidationError(
                'Project matching query does not exist'
            )

        if not project.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid project')
        return project.id

    def create(self, validated_data):
        project = validated_data.pop('project', None)
        af = super(AnalysisFrameworkSerializer, self).create(validated_data)

        if project:
            project = Project.objects.get(id=project)
            project.analysis_framework = af
            project.modified_by = self.context['request'].user
            project.save()

        return af

    def get_is_admin(self, analysis_framework):
        return analysis_framework.can_modify(self.context['request'].user)
