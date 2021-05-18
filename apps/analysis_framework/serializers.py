from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers, exceptions
from django.db.models import Q

from deep.serializers import RemoveNullFieldsMixin
from user_resource.serializers import UserResourceSerializer
from questionnaire.serializers import FrameworkQuestionSerializer
from user.models import User, Feature
from user.serializers import SimpleUserSerializer
from project.models import Project
from organization.serializers import SimpleOrganizationSerializer

from .models import (
    AnalysisFramework,
    AnalysisFrameworkRole,
    AnalysisFrameworkMembership,
    Widget, Filter, Exportable,
)


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


class AnalysisFrameworkRoleSerializer(
    RemoveNullFieldsMixin, DynamicFieldsMixin, serializers.ModelSerializer,
):
    class Meta:
        model = AnalysisFrameworkRole
        fields = ('__all__')


class AnalysisFrameworkMembershipSerializer(
    RemoveNullFieldsMixin, DynamicFieldsMixin, serializers.ModelSerializer,
):
    member_details = SimpleUserSerializer(read_only=True, source='member')
    role = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=AnalysisFrameworkRole.objects.all(),
    )
    added_by_details = SimpleUserSerializer(read_only=True, source='added_by')
    role_details = AnalysisFrameworkRoleSerializer(read_only=True, source='role')

    class Meta:
        model = AnalysisFrameworkMembership
        fields = ('__all__')

    def create(self, validated_data):
        user = self.context['request'].user
        framework = validated_data.get('framework')

        # NOTE: Default role is different for private and public framework
        # For public, two sorts of default role, one for non members and one while adding
        # member to af, which is editor role
        default_role = framework.get_or_create_default_role() if framework.is_private else\
            framework.get_or_create_editor_role()

        role = validated_data.get('role') or default_role

        if framework is None:
            raise serializers.ValidationError('Analysis Framework does not exist')

        membership = AnalysisFrameworkMembership.objects.filter(
            member=user,
            framework=framework,
        ).first()

        # If user is not a member of the private framework then return 404
        if membership is None and framework.is_private:
            raise exceptions.NotFound()
        elif membership is None:
            # Else if user is not member but is a public framework, return 403
            raise exceptions.PermissionDenied()

        # But if user is member and has no permissions, return 403
        if not membership.role.can_add_user:
            raise exceptions.PermissionDenied()

        if role.is_private_role and not framework.is_private:
            raise exceptions.PermissionDenied(
                {'message': 'Public framework cannot have private role'}
            )
        if not role.is_private_role and framework.is_private:
            raise exceptions.PermissionDenied(
                {'message': 'Private framework cannot have public role'}
            )

        validated_data['role'] = role  # Just in case role is not provided, add default role

        return super().create(validated_data)

    def delete(self, instance):
        user = self.context['request'].user
        member = instance.member
        if user == member:
            raise exceptions.PermissionDenied(
                {'message': 'You can not delete yourself'}
            )
        return super().delete(instance)


class AnalysisFrameworkSerializer(RemoveNullFieldsMixin, DynamicFieldsMixin, UserResourceSerializer):
    """
    Analysis Framework Model Serializer
    """
    widgets = SimpleWidgetSerializer(source='widget_set', many=True, required=False)
    filters = SimpleFilterSerializer(source='get_active_filters', many=True, read_only=True)
    exportables = SimpleExportableSerializer(source='exportable_set', many=True, read_only=True)
    questions = FrameworkQuestionSerializer(source='frameworkquestion_set', many=True, required=False, read_only=True)
    entries_count = serializers.IntegerField(
        source='get_entries_count',
        read_only=True,
    )

    is_admin = serializers.SerializerMethodField()
    users_with_add_permission = serializers.SerializerMethodField()
    visible_projects = serializers.SerializerMethodField()
    all_projects_count = serializers.IntegerField(source='project_set.count', read_only=True)

    project = serializers.IntegerField(
        write_only=True,
        required=False,
    )

    role = serializers.SerializerMethodField()
    organization_details = SimpleOrganizationSerializer(source='organization', read_only=True)

    class Meta:
        model = AnalysisFramework
        fields = ('__all__')

    def get_visible_projects(self, obj):
        from project.serializers import SimpleProjectSerializer
        user = None
        if 'request' in self.context:
            user = self.context['request'].user
        projects = obj.project_set.exclude(Q(is_private=True) & ~Q(members=user))
        return SimpleProjectSerializer(projects, context=self.context, many=True, read_only=True).data

    def get_users_with_add_permission(self, obj):
        """
        AF members with access to add other users to AF
        """
        return SimpleUserSerializer(
            User.objects.filter(
                id__in=obj.analysisframeworkmembership_set.filter(role__can_add_user=True).values('member'),
            ).all(),
            context=self.context,
            many=True,
        ).data

    def get_role(self, obj):
        user = self.context['request'].user
        membership = AnalysisFrameworkMembership.objects.filter(
            framework=obj,
            member=user
        ).first()

        role = None
        if not membership and not obj.is_private:
            role = obj.get_or_create_default_role()
        elif membership:
            role = membership.role
        else:
            return {}

        return AnalysisFrameworkRoleSerializer(role, context=self.context).data

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
        private = validated_data.get('is_private', False)

        # Check if user has access to private project feature
        user = self.context['request'].user
        private_access = user.profile.get_accessible_features().filter(
            key=Feature.PRIVATE_PROJECT
        ).exists()

        if private and not private_access:
            raise exceptions.PermissionDenied({
                "message": "You don't have permission to create private framework"
            })

        af = super().create(validated_data)

        if project:
            project = Project.objects.get(id=project)
            project.analysis_framework = af
            project.modified_by = user
            project.save()

        owner_role = af.get_or_create_owner_role()
        af.add_member(self.context['request'].user, owner_role)
        return af

    def update(self, instance, validated_data):
        if 'is_private' not in validated_data:
            return super().update(instance, validated_data)

        if instance.is_private != validated_data['is_private']:
            raise exceptions.PermissionDenied({
                "message": "You don't have permission to change framework's privacy"
            })
        return super().update(instance, validated_data)

    def get_is_admin(self, analysis_framework):
        return analysis_framework.can_modify(self.context['request'].user)
