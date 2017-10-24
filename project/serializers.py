from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer
from project.models import Project, ProjectMembership


class ProjectMembershipSerializer(DynamicFieldsMixin,
                                  serializers.ModelSerializer):
    member_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMembership
        fields = ('id', 'member', 'member_name',
                  'project', 'role', 'joined_at')

    def get_member_name(self, membership):
        return membership.member.profile.get_display_name()

    # Validations
    def validate_project(self, project):
        if not project.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid project')
        return project


class ProjectSerializer(DynamicFieldsMixin, UserResourceSerializer):
    memberships = ProjectMembershipSerializer(
        source='projectmembership_set',
        many=True, read_only=True
    )

    class Meta:
        model = Project
        fields = ('id', 'title', 'regions', 'memberships',
                  'user_groups', 'data',
                  'created_at', 'created_by', 'modified_at', 'modified_by',
                  'created_by_name', 'modified_by_name')
        read_only_fields = ('memberships', 'members',)

    def create(self, validated_data):
        project = super(ProjectSerializer, self).create(validated_data)
        ProjectMembership.objects.create(
            project=project,
            member=self.context['request'].user,
            role='admin',
        )
        return project

    # Validations
    def validate_user_groups(self, user_groups):
        for user_group in user_groups:
            if not user_group.can_modify(self.context['request'].user):
                raise serializers.ValidationError(
                    'Invalid user group: {}'.format(user_group.id))
        return user_groups

    def validate_regions(self, regions):
        for region in regions:
            if not region.can_modify(self.context['request'].user):
                raise serializers.ValidationError(
                    'Invalid region: {}'.format(region.id))
        return regions

    def validate_analysis_framework(self, analysis_framework):
        if not analysis_framework.can_modify(self.context['request'].user):
            raise serializers.ValidationError(
                'Invalid analysis framework: {}'.format(analysis_framework.id))
        return analysis_framework
