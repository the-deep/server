from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from geo.models import Region
from geo.serializers import SimpleRegionSerializer
from project.models import Project, ProjectMembership
from user_group.models import UserGroup
from user_group.serializers import SimpleUserGroupSerializer
from user_resource.serializers import UserResourceSerializer


class ProjectMembershipSerializer(DynamicFieldsMixin,
                                  serializers.ModelSerializer):
    member_email = serializers.CharField(source='member.email', read_only=True)
    member_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMembership
        fields = ('id', 'member', 'member_name', 'member_email',
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
        many=True,
        read_only=True,
    )
    regions = SimpleRegionSerializer(many=True, required=False)
    user_groups = SimpleUserGroupSerializer(many=True, required=False)
    role = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'start_date', 'end_date',
                  'regions', 'memberships', 'user_groups', 'data',
                  'analysis_framework', 'role',
                  'created_at', 'created_by', 'modified_at', 'modified_by',
                  'created_by_name', 'modified_by_name', 'version_id')
        read_only_fields = ('memberships', 'members',)

    def create(self, validated_data):
        project = super(ProjectSerializer, self).create(validated_data)
        ProjectMembership.objects.create(
            project=project,
            member=self.context['request'].user,
            role='admin',
        )
        return project

    def get_role(self, project):
        membership = ProjectMembership.objects.filter(
            project=project,
            member=self.context['request'].user
        ).first()
        if membership:
            return membership.role
        return None

    # Validations
    def validate_user_groups(self, user_groups):
        for user_group_obj in self.initial_data['user_groups']:
            user_group = UserGroup.objects.get(id=user_group_obj['id'])
            if self.instance and user_group in self.instance.user_groups.all():
                continue
            if not user_group.can_modify(self.context['request'].user):
                raise serializers.ValidationError(
                    'Invalid user group: {}'.format(user_group.id))
        return user_groups

    def validate_regions(self, data):
        for region_obj in self.initial_data['regions']:
            region = Region.objects.get(id=region_obj.get('id'))
            if self.instance and region in self.instance.regions.all():
                continue
            if not region.public and \
                    not region.can_modify(self.context['request'].user):
                raise serializers.ValidationError(
                    'Invalid region: {}'.format(region.id))
        return data

    def validate_analysis_framework(self, analysis_framework):
        if not analysis_framework.can_get(self.context['request'].user):
            raise serializers.ValidationError(
                'Invalid analysis framework: {}'.format(analysis_framework.id))
        return analysis_framework
