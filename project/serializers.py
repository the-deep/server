from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin
from geo.models import Region
from geo.serializers import SimpleRegionSerializer
from project.models import (
    Project,
    ProjectMembership,
    ProjectJoinRequest,
)
from user.serializers import SimpleUserSerializer
from user_group.models import UserGroup
from user_group.serializers import SimpleUserGroupSerializer
from user_resource.serializers import UserResourceSerializer


class SimpleProjectSerializer(RemoveNullFieldsMixin,
                              serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'title')


class ProjectMembershipSerializer(RemoveNullFieldsMixin,
                                  DynamicFieldsMixin,
                                  serializers.ModelSerializer):
    member_email = serializers.CharField(source='member.email', read_only=True)
    member_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMembership
        fields = '__all__'

    def get_unique_together_validators(self):
        return []

    def get_member_name(self, membership):
        return membership.member.profile.get_display_name()

    # Validations
    def validate_project(self, project):
        if not project.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid project')
        return project

    def create(self, validated_data):
        resource = super(ProjectMembershipSerializer, self)\
            .create(validated_data)
        resource.added_by = self.context['request'].user
        resource.save()
        return resource


class ProjectSerializer(RemoveNullFieldsMixin,
                        DynamicFieldsMixin, UserResourceSerializer):
    memberships = ProjectMembershipSerializer(
        source='projectmembership_set',
        many=True,
        required=False,
    )
    regions = SimpleRegionSerializer(many=True, required=False)
    user_groups = SimpleUserGroupSerializer(many=True, required=False)
    role = serializers.SerializerMethodField()

    analysis_framework_title = serializers.CharField(
        source='analysis_framework.title',
        read_only=True,
    )
    assessment_template_title = serializers.CharField(
        source='assessment_template.title',
        read_only=True,
    )
    category_editor_title = serializers.CharField(
        source='category_editor.title',
        read_only=True,
    )

    number_of_users = serializers.IntegerField(
        source='get_number_of_users',
        read_only=True,
    )

    number_of_leads = serializers.IntegerField(
        source='get_number_of_leads',
        read_only=True,
    )

    number_of_entries = serializers.IntegerField(
        source='get_number_of_entries',
        read_only=True,
    )

    entries_activity = serializers.ReadOnlyField(
        source='get_entries_activity',
    )
    leads_activity = serializers.ReadOnlyField(
        source='get_leads_activity',
    )

    status = serializers.IntegerField(
        source='get_status.id',
        read_only=True,
    )

    class Meta:
        model = Project
        exclude = ('members', )

    def create(self, validated_data):
        project = super(ProjectSerializer, self).create(validated_data)
        ProjectMembership.objects.create(
            project=project,
            member=self.context['request'].user,
            role='admin',
        )
        return project

    def get_role(self, project):
        request = self.context['request']
        user = request.GET.get('user', request.user)

        membership = ProjectMembership.objects.filter(
            project=project,
            member=user
        ).first()
        if membership:
            return membership.role

        group_membership = UserGroup.objects.filter(
            project=project,
            members=user,
        ).first()
        if group_membership:
            return 'normal'

        join_request = ProjectJoinRequest.objects.filter(
            project=project,
            requested_by=user,
        ).first()

        if join_request and (
            join_request.status == 'pending' or
            join_request.status == 'rejected'
        ):
            return join_request.status

        return 'none'

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


class ProjectJoinRequestSerializer(RemoveNullFieldsMixin,
                                   DynamicFieldsMixin,
                                   serializers.ModelSerializer):
    project = SimpleProjectSerializer(read_only=True)
    requested_by = SimpleUserSerializer(read_only=True)
    responded_by = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ProjectJoinRequest
        fields = '__all__'
