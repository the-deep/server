from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils.translation import gettext

from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from deep.permissions import AnalysisFrameworkPermissions as AfP
from deep.serializers import (
    RemoveNullFieldsMixin,
    URLCachedFileField,
    IntegerIDField,
    TempClientIdMixin,
    ProjectPropertySerializerMixin,
)
from geo.models import Region
from geo.serializers import SimpleRegionSerializer
from entry.models import Lead, Entry
from analysis_framework.models import AnalysisFrameworkMembership
from user.models import Feature
from user.serializers import SimpleUserSerializer
from user_group.models import UserGroup
from user.utils import (
    send_project_join_request_emails,
    send_project_accept_email,
    send_project_reject_email
)
from user_group.serializers import SimpleUserGroupSerializer
from user_resource.serializers import UserResourceSerializer, DeprecatedUserResourceSerializer
from ary.models import AssessmentTemplate

from .change_log import ProjectChangeManager
from .models import (
    Project,
    ProjectMembership,
    ProjectJoinRequest,
    ProjectRole,
    ProjectUserGroupMembership,
    ProjectOrganization,
    ProjectStats,
)

from organization.serializers import (
    SimpleOrganizationSerializer
)

from .permissions import PROJECT_PERMISSIONS
from .activity import project_activity_log


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


class ProjectSerializer(RemoveNullFieldsMixin, DynamicFieldsMixin, DeprecatedUserResourceSerializer):

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
            role=ProjectRole.get_owner_role(),
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
    DESCRIPTION_MIN_LENGTH = 50
    DESCRIPTION_MAX_LENGTH = 500

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
        if ProjectJoinRequest.objects.filter(project=project, requested_by=self.context['request'].user).exists():
            raise serializers.ValidationError("Already sent project join request for project %s" % project.title)
        return project

    def validate_reason(self, reason):
        if not (self.DESCRIPTION_MIN_LENGTH <= len(reason) <= self.DESCRIPTION_MAX_LENGTH):
            raise serializers.ValidationError(
                gettext("Must be at least %s characters and at most %s characters") % (
                    self.DESCRIPTION_MIN_LENGTH, self.DESCRIPTION_MAX_LENGTH,
                )
            )
        return reason


class ProjectAcceptRejectSerializer(serializers.ModelSerializer):
    role = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = ProjectJoinRequest
        fields = (
            'id',
            'status',
            'role'
        )

    @staticmethod
    def _accept_request(responded_by, join_request, role):
        if not role or role == 'normal':
            role = ProjectRole.get_default_role()
        elif role == 'admin':
            role = ProjectRole.get_admin_role()
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
        transaction.on_commit(
            lambda: send_project_accept_email.delay(join_request.id)
        )

    @staticmethod
    def _reject_request(responded_by, join_request):
        join_request.status = 'rejected'
        join_request.responded_by = responded_by
        join_request.responded_at = timezone.now()
        join_request.save()
        transaction.on_commit(
            lambda: send_project_reject_email.delay(join_request.id)
        )

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
        return instance


class ProjectMembershipGqlSerializer(TempClientIdMixin, serializers.ModelSerializer):
    id = IntegerIDField(required=False)
    role = serializers.PrimaryKeyRelatedField(required=False, queryset=ProjectRole.objects.all())

    class Meta:
        model = ProjectMembership
        fields = (
            'id', 'member', 'role', 'badges',
            'client_id',
        )

    @cached_property
    def project(self):
        project = self.context['request'].active_project
        # This is a rare case, just to make sure this is validated
        if self.instance and self.instance.project != project:
            raise serializers.ValidationError('Invalid access')
        return project

    @cached_property
    def current_user_role(self):
        return ProjectMembership.objects.get(
            project=self.project,
            member=self.context['request'].user,
        ).role

    def validate_member(self, member):
        if self.instance:  # Update
            if self.instance.member != member:
                # Changing member not allowed
                raise serializers.ValidationError('Changing member is not allowed!')
            return member
        # Create
        current_members = ProjectMembership.objects.filter(project=self.project, member=member)
        if current_members.exclude(pk=self.instance and self.instance.pk).exists():
            raise serializers.ValidationError('User is already a member!')
        return member

    def validate_role(self, new_role):
        # Make sure higher role are never allowed
        if new_role.level < self.current_user_role.level:
            raise serializers.ValidationError('Access is denied for higher role assignment.')
        if (
            self.instance and  # For Update
            self.instance.role != new_role and  # For changed role
            (
                self.instance.role.level == self.current_user_role.level and  # Requesting user role == current member role
                self.instance.role.level < new_role.level  # New role is lower then current role
            )
        ):
            raise serializers.ValidationError('Changing same level role is not allowed!')
        return new_role

    def validate(self, data):
        linked_group = (self.instance and self.instance.linked_group)
        if linked_group:
            raise serializers.ValidationError(
                f'This user is added through usergroup: {linked_group}. Please update the respective usergroup.'
            )
        return data

    def create(self, validated_data):
        validated_data['added_by'] = self.context['request'].user
        validated_data['project'] = self.project
        return super().create(validated_data)


class ProjectUserGroupMembershipGqlSerializer(TempClientIdMixin, serializers.ModelSerializer):
    class Meta:
        model = ProjectUserGroupMembership
        fields = (
            'id', 'usergroup', 'role', 'badges',
            'client_id',
        )

    @cached_property
    def project(self):
        project = self.context['request'].active_project
        # This is a rare case, just to make sure this is validated
        if self.instance and self.instance.project != project:
            raise serializers.ValidationError('Invalid access')
        return project

    @cached_property
    def current_user_role(self):
        return ProjectMembership.objects.get(
            project=self.project,
            member=self.context['request'].user,
        ).role

    def validate_usergroup(self, usergroup):
        if self.instance:  # Update
            if self.instance.usergroup != usergroup:
                # Changing usergroup not allowed
                raise serializers.ValidationError('Changing usergroup is not allowed!')
            return usergroup
        # Create
        current_usergroup_members = ProjectUserGroupMembership.objects.filter(project=self.project, usergroup=usergroup)
        if current_usergroup_members.exclude(pk=self.instance and self.instance.pk).exists():
            raise serializers.ValidationError('UserGroup already a member!')
        return usergroup

    def validate_role(self, new_role):
        if new_role.level < self.current_user_role.level:
            raise serializers.ValidationError('Access is denied for higher role assignment.')
        if (
            self.instance and  # Update
            self.instance.role != new_role and  # Role is changed
            (
                self.instance.role.level == self.current_user_role.level and  # Requesting user role == current member role
                self.instance.role.level < new_role.level  # New role is lower then current role
            )
        ):
            raise serializers.ValidationError('Changing same level role is not allowed!')
        return new_role

    def create(self, validated_data):
        validated_data['project'] = self.project
        validated_data['added_by'] = self.context['request'].user
        return super().create(validated_data)


class ProjectVizConfigurationSerializer(ProjectPropertySerializerMixin, serializers.ModelSerializer):
    class Action(models.TextChoices):
        NEW = 'new', 'New'
        ON = 'on', 'On'
        OFF = 'off', 'Off'

    class Meta:
        model = ProjectStats
        fields = ('action',)

    action = serializers.ChoiceField(choices=Action.choices)

    def validate(self, data):
        if not self.project.is_visualization_available:
            raise serializers.ValidationError('Visualization is not available for this project')
        return data

    def save(self):
        action = self.validated_data and self.validated_data['action']
        return self.project.project_stats.update_public_share_configuration(action)


class ProjectOrganizationGqSerializer(TempClientIdMixin, serializers.ModelSerializer):
    id = IntegerIDField(required=False)

    class Meta:
        model = ProjectOrganization
        fields = (
            'id', 'organization', 'organization_type',
            'client_id',
        )


class ProjectGqSerializer(DeprecatedUserResourceSerializer):
    organizations = ProjectOrganizationGqSerializer(source='projectorganization_set', many=True, required=False)

    class Meta:
        model = Project
        fields = (
            'title',
            'description',
            'start_date',
            'end_date',
            'status',
            'is_private',
            'is_test',
            'is_assessment_enabled',
            'analysis_framework',
            'is_visualization_enabled',
            'has_publicly_viewable_unprotected_leads',
            'has_publicly_viewable_restricted_leads',
            'has_publicly_viewable_confidential_leads',
            'enable_publicly_viewable_analysis_report_snapshot',
            'organizations',
        )

    # NOTE: This is a custom function (apps/user_resource/serializers.py::UserResourceSerializer)
    # This makes sure only scoped (individual entry) instances (attributes) are updated.
    def _get_prefetch_related_instances_qs(self, qs):
        if self.instance:
            return qs.filter(project=self.instance)
        return qs.none()  # On create throw error if existing id is provided

    @cached_property
    def current_user(self):
        return self.context['request'].user

    def validate_is_private(self, is_private):
        if self.instance:
            # For update, don't allow changing privacy.
            if self.instance.is_private != is_private:
                raise serializers.ValidationError('Cannot change privacy of project.')
        # For create, make sure user can feature permission to create private project.
        else:
            private_access = self.current_user.profile.\
                get_accessible_features().filter(key=Feature.FeatureKey.PRIVATE_PROJECT)
            if is_private and not private_access.exists():
                raise serializers.ValidationError("You don't have permission to create private project")
        return is_private

    def validate_analysis_framework(self, framework):
        if (self.instance and self.instance.analysis_framework) == framework:
            return framework
        if not framework.can_get(self.current_user):
            raise serializers.ValidationError(
                "Given framework either doesn't exists or you don't have access to it"
            )
        if not framework.is_private:
            return framework
        # Check membership+permissions if private
        allowed_permission = AfP.get_permissions(framework.get_current_user_role(self.current_user))
        if not allowed_permission:
            raise serializers.ValidationError("Either framework doesn't exists or you don't have access")
        if AfP.Permission.CAN_USE_IN_OTHER_PROJECTS not in allowed_permission:
            raise serializers.ValidationError("You don't have permissions to use the analysis framework in the project")
        return framework

    def validate(self, data):
        is_private = data.get('is_private', self.instance and self.instance.is_private)
        framework = data.get('analysis_framework', self.instance and self.instance.analysis_framework)

        # Analysis Frameowrk check
        if (self.instance and self.instance.analysis_framework) != framework:
            # Check private
            if not is_private and framework.is_private:
                raise serializers.ValidationError({
                    'analysis_framework': 'Cannot use private framework in public project',
                })
        return data

    def validate_title(self, title):
        existing_projects = Project.objects.filter(title__iexact=title)
        if self.instance:
            existing_projects = existing_projects.exclude(id=self.instance.id)
        if existing_projects.exists():
            raise serializers.ValidationError(
                f'Project title "{title}" already exists, please provide different title',
            )
        return title

    def create(self, validated_data):
        project = super().create(validated_data)
        ProjectMembership.objects.create(
            project=project,
            member=self.current_user,
            role=ProjectRole.get_owner_role(),
        )
        ProjectChangeManager.log_project_created(project, self.current_user)
        return project
