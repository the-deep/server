from django.db import models
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from deep.serializers import RemoveNullFieldsMixin
from geo.models import Region
from geo.serializers import SimpleRegionSerializer
from project.models import (
    Project,
    ProjectMembership,
    ProjectJoinRequest,
    ProjectRole,
    ProjectUserGroupMembership,
    ProjectStatusCondition,
)
from entry.models import Lead, Entry
from project.permissions import PROJECT_PERMISSIONS
from project.activity import project_activity_log

from user.serializers import SimpleUserSerializer
from user_group.models import UserGroup
from user_group.serializers import SimpleUserGroupSerializer
from user_resource.serializers import UserResourceSerializer


class SimpleProjectSerializer(RemoveNullFieldsMixin,
                              serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'title')


class ProjectRoleSerializer(RemoveNullFieldsMixin,
                            DynamicFieldsMixin,
                            serializers.ModelSerializer):
    lead_permissions = serializers.SerializerMethodField()
    entry_permissions = serializers.SerializerMethodField()
    setup_permissions = serializers.SerializerMethodField()
    export_permissions = serializers.SerializerMethodField()
    assessment_permissions = serializers.SerializerMethodField()

    class Meta:
        model = ProjectRole
        fields = '__all__'

    def get_lead_permissions(self, roleobj):
        return [
            k
            for k, v in PROJECT_PERMISSIONS['lead'].items()
            if roleobj.lead_permissions & v != 0
        ]

    def get_entry_permissions(self, roleobj):
        return [
            k
            for k, v in PROJECT_PERMISSIONS['entry'].items()
            if roleobj.entry_permissions & v != 0
        ]

    def get_setup_permissions(self, roleobj):
        return [
            k
            for k, v in PROJECT_PERMISSIONS['setup'].items()
            if roleobj.setup_permissions & v != 0
        ]

    def get_export_permissions(self, roleobj):
        return [
            k
            for k, v in PROJECT_PERMISSIONS['export'].items()
            if roleobj.export_permissions & v != 0
        ]

    def get_assessment_permissions(self, roleobj):
        return [
            k
            for k, v in PROJECT_PERMISSIONS['assessment'].items()
            if roleobj.assessment_permissions & v != 0
        ]


class SimpleProjectRoleSerializer(RemoveNullFieldsMixin,
                                  DynamicFieldsMixin,
                                  serializers.ModelSerializer):
    class Meta:
        model = ProjectRole
        fields = ('id', 'title')


class ProjectDashboardSerializer(RemoveNullFieldsMixin,
                                 DynamicFieldsMixin,
                                 serializers.ModelSerializer):

    created_by = serializers.CharField(
        source='created_by.profile.get_display_name',
        read_only=True,
    )
    created_by_id = serializers.IntegerField(
        source='created_by.profile.id',
        read_only=True,
    )
    regions = SimpleRegionSerializer(many=True, required=False)
    number_of_users = serializers.IntegerField(
        source='get_number_of_users',
        read_only=True,
    )
    number_of_leads = serializers.IntegerField(read_only=True)
    number_of_entries = serializers.IntegerField(read_only=True)
    status = serializers.ReadOnlyField(source='status.title')

    leads_activity = serializers.ReadOnlyField(source='get_leads_activity')
    entries_activity = serializers.ReadOnlyField(source='get_entries_activity')

    top_sourcers = serializers.SerializerMethodField()
    top_taggers = serializers.SerializerMethodField()
    activity_log = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('created_at', 'created_by', 'created_by_id', 'regions',
                  'top_sourcers', 'top_taggers', 'status', 'activity_log',
                  'number_of_users', 'number_of_leads', 'number_of_entries',
                  'leads_activity', 'entries_activity')

    def get_top_sourcers(self, project):
        sourcers = ProjectMembership.objects.filter(
            project=project,
        ).annotate(
            leads_count=models.functions.Coalesce(models.Subquery(
                Lead.objects.filter(
                    project=project,
                    created_by=models.OuterRef('member'),
                ).order_by().values('project')
                .annotate(cnt=models.Count('*')).values('cnt')[:1],
                output_field=models.IntegerField(),
            ), 0),
        ).order_by('-leads_count')[:5]

        return [
            {
                'id': sourcer.id,
                'name': sourcer.member.profile.get_display_name(),
                'user_id': sourcer.member.id,
                'count': sourcer.leads_count,
            } for sourcer in sourcers
        ]

    def get_top_taggers(self, project):
        taggers = ProjectMembership.objects.filter(
            project=project,
        ).annotate(
            entries_count=models.functions.Coalesce(models.Subquery(
                Entry.objects.filter(
                    project=project,
                    created_by=models.OuterRef('member'),
                ).order_by().values('project')
                .annotate(cnt=models.Count('*')).values('cnt')[:1],
                output_field=models.IntegerField(),
            ), 0),
        ).order_by('-entries_count')[:5]

        return [
            {
                'id': tagger.id,
                'name': tagger.member.profile.get_display_name(),
                'user_id': tagger.member.id,
                'count': tagger.entries_count,
            } for tagger in taggers
        ]

    def get_activity_log(self, project):
        return list(project_activity_log(project))


class ProjectMembershipSerializer(RemoveNullFieldsMixin,
                                  DynamicFieldsMixin,
                                  serializers.ModelSerializer):
    member_email = serializers.CharField(source='member.email', read_only=True)
    member_name = serializers.CharField(
        source='member.profile.get_display_name', read_only=True)
    member_status = serializers.SerializerMethodField()
    member_organization = serializers.CharField(
        source='member.profile.organization',
        read_only=True,
    )
    user_group_options = SimpleUserGroupSerializer(
        source='get_user_group_options',
        read_only=True,
        many=True,
    )

    class Meta:
        model = ProjectMembership
        fields = '__all__'

    def get_member_status(self, membership):
        if ProjectRole.get_admin_roles().filter(
                id=membership.role.id
        ).exists():
            return 'admin'
        return 'member'

    # Validations
    def validate_project(self, project):
        if not project.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid project')
        return project

    def validate(self, data):
        role = data.get('role')
        if not role:
            return data

        project = data.get('project',
                           self.instance and self.instance.project)
        user = self.context['request'].user
        user_role = ProjectMembership.objects.filter(
            project=project,
            member=user,
        ).first().role

        if role.level < user_role.level:
            raise serializers.ValidationError('Invalid role')
        return data

    def create(self, validated_data):
        resource = super().create(validated_data)
        resource.added_by = self.context['request'].user
        resource.save()
        return resource


class ProjectUsergroupMembershipSerializer(RemoveNullFieldsMixin,
                                           DynamicFieldsMixin,
                                           serializers.ModelSerializer):
    group_title = serializers.CharField(source='usergroup.title')

    class Meta:
        model = ProjectUserGroupMembership
        fields = '__all__'

    def get_unique_together_validators(self):
        return []

    # Validations
    def validate_project(self, project):
        if not project.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid project')
        return project

    def create(self, validated_data):
        resource = super().create(validated_data)
        resource.added_by = self.context['request'].user
        resource.save()
        return resource


class ProjectSerializer(RemoveNullFieldsMixin,
                        DynamicFieldsMixin, UserResourceSerializer):
    memberships = ProjectMembershipSerializer(
        source='projectmembership_set',
        many=True,
        read_only=True,
    )

    regions = SimpleRegionSerializer(many=True, required=False)
    role = serializers.SerializerMethodField()

    member_status = serializers.SerializerMethodField()

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

    user_groups = SimpleUserGroupSerializer(many=True, read_only=True)

    number_of_users = serializers.IntegerField(
        source='get_number_of_users',
        read_only=True,
    )
    number_of_leads = serializers.IntegerField(read_only=True)
    number_of_entries = serializers.IntegerField(read_only=True)

    entries_activity = serializers.ReadOnlyField(
        source='get_entries_activity',
    )
    leads_activity = serializers.ReadOnlyField(
        source='get_leads_activity',
    )

    status_title = serializers.ReadOnlyField(source='status.title')

    class Meta:
        model = Project
        exclude = ('members', )

    def create(self, validated_data):
        project = super().create(validated_data)
        ProjectMembership.objects.create(
            project=project,
            member=self.context['request'].user,
            role=ProjectRole.get_creator_role(),
        )
        return project

    def get_member_status(self, project):
        request = self.context['request']
        user = request.GET.get('user', request.user)

        role = project.get_role(user)
        if role:
            if ProjectRole.get_admin_roles().filter(id=role.id).exists():
                return 'admin'
            return 'member'

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

    def get_role(self, project):
        request = self.context['request']
        user = request.GET.get('user', request.user)

        membership = ProjectMembership.objects.filter(
            project=project,
            member=user
        ).first()
        if membership:
            return membership.role.id
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


class ProjectJoinRequestSerializer(RemoveNullFieldsMixin,
                                   DynamicFieldsMixin,
                                   serializers.ModelSerializer):
    project = SimpleProjectSerializer(read_only=True)
    requested_by = SimpleUserSerializer(read_only=True)
    responded_by = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ProjectJoinRequest
        fields = '__all__'


class ProjectEntitySerializer(UserResourceSerializer):

    def create(self, validated_data):
        user = self.context['request'].user
        project = validated_data['project']
        role = project.get_role(user)

        if not role or not role.can_create_lead:
            raise PermissionDenied(
                {'message': "You don't have permission to create lead"}
            )
        return super().create(validated_data)


class ProjectUserGroupSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='usergroup.title', read_only=True)

    class Meta:
        model = ProjectUserGroupMembership
        fields = '__all__'


class ProjectStatusConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectStatusCondition
        fields = '__all__'
