from django.db import models
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils.translation import gettext

from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from deep.serializers import RemoveNullFieldsMixin, URLCachedFileField, IntegerIDField
from geo.models import Region
from geo.serializers import SimpleRegionSerializer
from entry.models import Lead, Entry
from analysis_framework.models import AnalysisFrameworkMembership
from user.models import Feature
from user.serializers import SimpleUserSerializer
from user_group.models import UserGroup
from user.utils import send_project_join_request_emails
from user_group.serializers import SimpleUserGroupSerializer
from user_resource.serializers import UserResourceSerializer
from ary.models import AssessmentTemplate
from .models import (
    Project,
    ProjectMembership,
    ProjectJoinRequest,
    ProjectRole,
    ProjectUserGroupMembership,
    ProjectOrganization,
)

from organization.serializers import (
    SimpleOrganizationSerializer
)

from .permissions import PROJECT_PERMISSIONS
from .activity import project_activity_log

MIN_LENGTH = 50


class SimpleProjectSerializer(RemoveNullFieldsMixin,
                              serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'title', 'is_private')


class ProjectNotificationSerializer(RemoveNullFieldsMixin, serializers.ModelSerializer):
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
        fields = ('id', 'title', 'level')


class ProjectOrganizationSerializer(RemoveNullFieldsMixin,
                                    DynamicFieldsMixin,
                                    UserResourceSerializer,
                                    serializers.ModelSerializer):
    organization_type_display = serializers.CharField(source='get_organization_type_display', read_only=True)
    organization_details = SimpleOrganizationSerializer(source='organization', read_only=True)

    class Meta:
        model = ProjectOrganization
        fields = ('id', 'organization', 'organization_details', 'organization_type', 'organization_type_display')


class ProjectMembershipSerializer(RemoveNullFieldsMixin,
                                  DynamicFieldsMixin,
                                  serializers.ModelSerializer):
    member_email = serializers.CharField(source='member.email', read_only=True)
    member_name = serializers.CharField(
        source='member.profile.get_display_name', read_only=True)
    added_by_name = serializers.CharField(
        source='added_by.profile.get_display_name',
        read_only=True,
    )
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
    role_details = SimpleProjectRoleSerializer(source='role', read_only=True)

    class Meta:
        model = ProjectMembership
        fields = '__all__'
        read_only_fields = ('project',)

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

    def project_member_validation(self, project, member):
        if ProjectMembership.objects.filter(
            project=project,
            member=member
        ).exists():
            raise serializers.ValidationError({'member': 'Member already exist'})

    def validate(self, data):
        data['project_id'] = int(self.context['view'].kwargs['project_id'])
        member = data.get('member')
        if not self.instance:
            self.project_member_validation(data['project_id'], member)
        role = data.get('role')
        if not role:
            return data
        user = self.context['request'].user
        user_role = ProjectMembership.objects.filter(
            project=data['project_id'],
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


class ProjectSerializer(RemoveNullFieldsMixin, DynamicFieldsMixin, UserResourceSerializer):

    organizations = ProjectOrganizationSerializer(
        source='projectorganization_set',
        many=True,
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

    number_of_users = serializers.IntegerField(read_only=True)
    is_visualization_enabled = serializers.SerializerMethodField(read_only=True)
    has_assessments = serializers.BooleanField(required=False)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Project
        exclude = ('members', 'stats_cache')

    def create(self, validated_data):
        member = self.context['request'].user
        is_private = validated_data.get('is_private', False)

        private_access = member.profile.get_accessible_features().filter(
            key=Feature.FeatureKey.PRIVATE_PROJECT
        ).exists()

        if is_private and not private_access:
            raise PermissionDenied(
                {'message': "You don't have permission to create private project"}
            )

        project = super().create(validated_data)
        ProjectMembership.objects.create(
            project=project,
            member=member,
            role=ProjectRole.get_creator_role(),
        )

        return project

    def update(self, instance, validated_data):
        # TODO; might need to check for private project feature access,
        # But that might be redundant, since checked in creation, I don't know
        framework = validated_data.get('analysis_framework')
        user = self.context['request'].user

        if 'is_private' in validated_data and\
                validated_data['is_private'] != instance.is_private:
            raise PermissionDenied('Cannot change privacy of project')

        if framework is None or not framework.is_private:
            return super().update(instance, validated_data)

        if not instance.is_private and framework.is_private:
            raise PermissionDenied('Cannot use private framework in public project')

        memberships = AnalysisFrameworkMembership.objects.filter(
            framework=framework,
            member=user,
        )
        if not memberships.exists():
            # Send a bad request, use should not know if the framework exists
            raise serializers.ValidationError('Invalid Analysis Framework')

        if memberships.filter(role__can_use_in_other_projects=True).exists():
            return super().update(instance, validated_data)

        raise PermissionDenied(
            {'message': "You don't have permissions to use the analysis framework in the project"}
        )

    def validate(self, data):
        has_assessments = data.pop('has_assessments', None)
        if has_assessments is not None:
            data['assessment_template'] = AssessmentTemplate.objects.first() if has_assessments else None
        return data

    def get_is_visualization_enabled(self, project):
        af = project.analysis_framework
        is_viz_enabled = project.is_visualization_enabled
        entry_viz_enabled = (
            is_viz_enabled and
            af.properties is not None and
            af.properties.get('stats_config') is not None
        )
        # Entry viz data is required by ARY VIZ
        ary_viz_enabled = entry_viz_enabled

        return {
            'entry': entry_viz_enabled,
            'assessment': ary_viz_enabled,
        }

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


class ProjectMemberViewSerializer(ProjectSerializer):
    memberships = ProjectMembershipSerializer(
        source='projectmembership_set',
        many=True,
        read_only=True,
    )


class ProjectStatSerializer(ProjectSerializer):
    number_of_leads = serializers.IntegerField(read_only=True)
    number_of_leads_tagged = serializers.IntegerField(read_only=True)
    number_of_leads_tagged_and_controlled = serializers.IntegerField(read_only=True)
    number_of_entries = serializers.IntegerField(read_only=True)

    leads_activity = serializers.ReadOnlyField(source='get_leads_activity')
    entries_activity = serializers.ReadOnlyField(source='get_entries_activity')

    top_sourcers = serializers.SerializerMethodField()
    top_taggers = serializers.SerializerMethodField()
    activity_log = serializers.SerializerMethodField()

    def _get_top_entity_contributer(self, project, Entity):
        contributers = ProjectMembership.objects.filter(
            project=project,
        ).annotate(
            entity_count=models.functions.Coalesce(models.Subquery(
                Entity.objects.filter(
                    project=project,
                    created_by=models.OuterRef('member'),
                ).order_by().values('project')
                .annotate(cnt=models.Count('*')).values('cnt')[:1],
                output_field=models.IntegerField(),
            ), 0),
        ).order_by('-entity_count').select_related('member', 'member__profile')[:5]

        return [
            {
                'id': contributer.id,
                'name': contributer.member.profile.get_display_name(),
                'user_id': contributer.member.id,
                'count': contributer.entity_count,
            } for contributer in contributers
        ]

    def get_top_sourcers(self, project):
        return self._get_top_entity_contributer(project, Lead)

    def get_top_taggers(self, project):
        return self._get_top_entity_contributer(project, Entry)

    def get_activity_log(self, project):
        return list(project_activity_log(project))


class ProjectJoinRequestSerializer(RemoveNullFieldsMixin,
                                   DynamicFieldsMixin,
                                   serializers.ModelSerializer):
    project = SimpleProjectSerializer(read_only=True)
    requested_by = SimpleUserSerializer(read_only=True)
    responded_by = SimpleUserSerializer(read_only=True)
    # `reason`  will be stored into json field
    reason = serializers.CharField(source='data.reason', required=True)

    class Meta:
        model = ProjectJoinRequest
        fields = '__all__'

    def create(self, validated_data):
        validated_data['project'] = self.context['project']
        validated_data['requested_by'] = self.context['request'].user
        validated_data['status'] = 'pending'
        return super(ProjectJoinRequestSerializer, self).create(validated_data)


class ProjectUserGroupSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='usergroup.title', read_only=True)
    role_details = SimpleProjectRoleSerializer(source='role', read_only=True)
    added_by_name = serializers.CharField(source='added_by.profile.get_display_name', read_only=True)

    class Meta:
        model = ProjectUserGroupMembership
        fields = '__all__'
        read_only_fields = ('project',)

    def validate(self, data):
        data['project_id'] = int(self.context['view'].kwargs['project_id'])
        usergroup = data.get('usergroup')
        if usergroup and ProjectUserGroupMembership.objects.filter(project=data['project_id'],
                                                                   usergroup=usergroup).exists():
            raise serializers.ValidationError({'usergroup': 'Usergroup already exist in the project'})
        return data

    def create(self, validated_data):
        project_user_group_membership = super().create(validated_data)
        project_user_group_membership.added_by = self.context['request'].user
        project_user_group_membership.save(update_fields=['added_by'])
        return project_user_group_membership


class ProjectRecentActivitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    project = serializers.IntegerField()
    project_display_name = serializers.CharField()
    created_by = serializers.IntegerField()
    created_by_display_picture = serializers.SerializerMethodField()
    type = serializers.CharField()
    created_by_display_name = serializers.CharField()

    def get_created_by_display_picture(self, instance):
        name = instance['created_by_display_picture']
        return name and self.context['request'].build_absolute_uri(URLCachedFileField.name_to_representation(name))


# -------Graphql Serializer
class ProjectJoinGqSerializer(serializers.ModelSerializer):
    project = serializers.CharField(required=True)
    reason = serializers.CharField(source='data.reason', required=True)
    role = serializers.CharField(required=False)
    requested_by = serializers.CharField(read_only=True)
    responded_by = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = ProjectJoinRequest
        fields = (
            'id',
            'reason',
            'role',
            'requested_by',
            'responded_by',
            'project',
            'status',
            'data'
        )

    def create(self, validated_data):
        validated_data['requested_by'] = self.context['request'].user
        validated_data['status'] = ProjectJoinRequest.Status.PENDING
        validated_data['role_id'] = ProjectRole.get_default_role().id
        instance = super().create(validated_data)
        transaction.on_commit(
            lambda: send_project_join_request_emails.delay(instance.id)
        )
        return instance

    def validate_project(self, project):
        project = get_object_or_404(Project, id=project)
        if project.is_private:
            raise serializers.ValidationError("Cannot join private project")
        if ProjectMembership.objects.filter(project=project, member=self.context['request'].user).exists():
            raise serializers.ValidationError("Already a member")
        return project

    def validate_reason(self, reason):
        if len(reason) <= MIN_LENGTH:
            raise serializers.ValidationError(gettext("Must be at least %s characters") % MIN_LENGTH)
        return reason


class ProjectAcceptRejectSerializer(serializers.ModelSerializer):
    id = IntegerIDField(required=False)
    status = serializers.CharField(required=True)
    role = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = ProjectJoinRequest
        fields = ('id', 'status', 'role')

    @staticmethod
    def _accept_request(responded_by, join_request, role):
        if not role or role == 'normal':
            role = ProjectRole.get_default_role()
        elif role == 'admin':
            role = ProjectRole.get_default_admin_role()
        else:
            role_qs = ProjectRole.objects.filter(id=role)
            if not role_qs.exists():
                raise serializers.ValidationError('Role doesnot exist')
            role = role_qs.first()

        join_request.status = 'accepted'
        join_request.responded_by = responded_by
        join_request.responded_at = timezone.now()
        join_request.role = role
        join_request.save()

        ProjectMembership.objects.update_or_create(
            project=join_request.project,
            member=join_request.requested_by,
            defaults={
                'role': role,
                'added_by': responded_by,
            },
        )

    @staticmethod
    def _reject_request(responded_by, join_request):
        join_request.status = 'rejected'
        join_request.responded_by = responded_by
        join_request.responded_at = timezone.now()
        join_request.save()

    def update(self, instance, validated_data):
        validated_data['project'] = self.context['request'].active_project
        role = validated_data.pop('role', None)
        if instance.status in ['accepted', 'rejected']:
            raise serializers.ValidationError(
                'This request has already been {}'.format(instance.status)
            )
        if validated_data['status'] == 'accepted':
            ProjectAcceptRejectSerializer._accept_request(self.context['request'].user, instance, role)
        elif validated_data['status'] == 'rejected':
            ProjectAcceptRejectSerializer._reject_request(self.context['request'].user, instance)
        return super().update(instance, validated_data)
