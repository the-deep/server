from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers, exceptions

from deep.serializers import RemoveNullFieldsMixin
from user_resource.serializers import UserResourceSerializer
from analysis_framework.models import (
    AnalysisFramework,
    AnalysisFrameworkRole,
    AnalysisFrameworkMembership,
    Widget, Filter, Exportable
)
from project.models import Project


class WidgetSerializer(RemoveNullFieldsMixin,
                       DynamicFieldsMixin, serializers.ModelSerializer):
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


class FilterSerializer(RemoveNullFieldsMixin,
                       DynamicFieldsMixin, serializers.ModelSerializer):
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


class ExportableSerializer(RemoveNullFieldsMixin,
                           DynamicFieldsMixin, serializers.ModelSerializer):
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


class SimpleWidgetSerializer(RemoveNullFieldsMixin,
                             serializers.ModelSerializer):
    class Meta:
        model = Widget
        fields = ('id', 'key', 'widget_id', 'title', 'properties')


class SimpleFilterSerializer(RemoveNullFieldsMixin,
                             serializers.ModelSerializer):
    class Meta:
        model = Filter
        fields = ('id', 'key', 'widget_key', 'title',
                  'properties', 'filter_type')


class SimpleExportableSerializer(RemoveNullFieldsMixin,
                                 serializers.ModelSerializer):
    class Meta:
        model = Exportable
        fields = ('id', 'widget_key', 'inline', 'order', 'data')


class AnalysisFrameworkSerializer(RemoveNullFieldsMixin,
                                  DynamicFieldsMixin, UserResourceSerializer):
    """
    Analysis Framework Model Serializer
    """
    widgets = SimpleWidgetSerializer(source='widget_set',
                                     many=True,
                                     required=False)
    filters = SimpleFilterSerializer(source='filter_set',
                                     many=True,
                                     read_only=True)
    exportables = SimpleExportableSerializer(source='exportable_set',
                                             many=True,
                                             read_only=True)
    entries_count = serializers.IntegerField(
        source='get_entries_count',
        read_only=True,
    )

    is_admin = serializers.SerializerMethodField()

    project = serializers.IntegerField(
        write_only=True,
        required=False,
    )

    class Meta:
        model = AnalysisFramework
        fields = ('__all__')

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
        af = super().create(validated_data)

        if project:
            project = Project.objects.get(id=project)
            project.analysis_framework = af
            project.modified_by = self.context['request'].user
            project.save()

        owner_role = af.get_or_create_owner_role()
        af.add_member(self.context['request'].user, owner_role)
        return af

    def update(self, instance, validated_data):
        if 'is_private' not in validated_data:
            return super().update(instance, validated_data)

        if instance.is_private != validated_data['is_private']:
            raise exceptions.PermissionDenied('Cannot change privacy of project')
        return super().update(instance, validated_data)

    def get_is_admin(self, analysis_framework):
        return analysis_framework.can_modify(self.context['request'].user)


class AnalysisFrameworkMembershipSerializer(
    RemoveNullFieldsMixin, DynamicFieldsMixin, serializers.ModelSerializer,
):
    class Meta:
        model = AnalysisFrameworkMembership
        fields = ('__all__')

    def create(self, validated_data):
        user = self.context['request'].user
        framework = validated_data.get('framework')

        if framework is None:
            raise serializers.ValidationError('Analysis Framework does not exist')

        can_create = AnalysisFrameworkMembership.objects.filter(
            member=user,
            framework=framework,
            role__can_add_user=True
        ).exists()

        if not can_create:
            raise exceptions.PermissionDenied()

        return super().create(validated_data)


class AnalysisFrameworkRoleSerializer(
    RemoveNullFieldsMixin, DynamicFieldsMixin, serializers.ModelSerializer,
):
    class Meta:
        model = AnalysisFrameworkRole
        fields = ('__all__')
