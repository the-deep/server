from django.utils.functional import cached_property
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin, TempClientIdMixin, IntegerIDField
from user_group.models import UserGroup, GroupMembership
from user_resource.serializers import UserResourceSerializer


class SimpleUserGroupSerializer(RemoveNullFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = ('id', 'title')


class GroupMembershipSerializer(
    RemoveNullFieldsMixin,
    DynamicFieldsMixin,
    serializers.ModelSerializer
):
    member_email = serializers.CharField(source='member.email', read_only=True)
    member_name = serializers.SerializerMethodField()

    class Meta:
        model = GroupMembership
        fields = ('id', 'member', 'member_name', 'member_email',
                  'group', 'role', 'joined_at')

    def get_member_name(self, membership):
        return membership.member.profile.get_display_name()

    # Validations
    def validate_group(self, group):
        if not group.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid user group')
        return group

    def create(self, validated_data):
        resource = super()\
            .create(validated_data)
        resource.added_by = self.context['request'].user
        resource.save()
        return resource


class UserGroupSerializer(
    RemoveNullFieldsMixin,
    DynamicFieldsMixin,
    UserResourceSerializer
):
    memberships = GroupMembershipSerializer(
        source='groupmembership_set',
        many=True,
        required=False,
    )
    role = serializers.SerializerMethodField()
    members_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = UserGroup
        fields = (
            'id', 'title', 'description', 'display_picture', 'role',
            'memberships', 'global_crisis_monitoring',
            'custom_project_fields', 'created_at', 'modified_at',
            'created_by', 'modified_by', 'members_count'
        )

    def create(self, validated_data):
        user_group = super().create(validated_data)
        GroupMembership.objects.create(
            group=user_group,
            member=self.context['request'].user,
            role='admin'
        )
        return user_group

    def get_role(self, user_group):
        request = self.context['request']
        user = request.GET.get('user', request.user)

        membership = GroupMembership.objects.filter(
            group=user_group,
            member=user
        ).first()
        if membership:
            return membership.role
        return 'null'


# ------------------------ Graphql mutation serializers -------------------------------


class GroupMembershipGqSerializer(
    RemoveNullFieldsMixin,
    DynamicFieldsMixin,
    serializers.ModelSerializer
):
    class Meta:
        model = GroupMembership
        fields = ('id', 'member', 'role',)

    # Validations
    def validate_group(self, group):
        # TODO: Use permission check in mutation
        if not group.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid user group')
        return group

    def create(self, validated_data):
        resource = super().create(validated_data)
        resource.added_by = self.context['request'].user
        resource.save()
        return resource


class UserGroupGqSerializer(
    RemoveNullFieldsMixin,
    DynamicFieldsMixin,
    UserResourceSerializer
):
    class Meta:
        model = UserGroup
        fields = (
            'id', 'title', 'description', 'display_picture', 'global_crisis_monitoring', 'custom_project_fields',
        )

    def create(self, validated_data):
        user_group = super().create(validated_data)
        GroupMembership.objects.create(
            group=user_group,
            member=self.context['request'].user,
            role='admin'
        )
        return user_group

    def update(self, instance, validated_data):
        user_group = super().update(instance, validated_data)
        # FIXME: Adding created_by as admin if removed after update
        if user_group.created_by and not user_group.members.filter(pk=user_group.created_by_id).exists():
            GroupMembership.objects.create(
                group=user_group,
                member=user_group.created_by,
                role='admin'
            )
        return user_group


class UserGroupMembershipGqlSerializer(TempClientIdMixin, serializers.ModelSerializer):
    id = IntegerIDField(required=False)

    class Meta:
        model = GroupMembership
        fields = (
            'id',
            'member',
            'role',
            'client_id'
        )

    @cached_property
    def usergroup(self):
        usergroup = self.context['request'].active_ug
        # This is a rare case, just to make sure this is validated
        if self.instance and self.instance.group != usergroup:
            raise serializers.ValidationError('Invalid access')
        return usergroup

    def validate_member(self, member):
        current_members = GroupMembership.objects.filter(group=self.usergroup, member=member)
        if current_members.exclude(pk=self.instance and self.instance.pk).exists():
            raise serializers.ValidationError('User is already a member!')
        return member

    def create(self, validated_data):
        # make request user to be added_by by default
        validated_data['added_by'] = self.context['request'].user
        validated_data['group'] = self.usergroup
        return super().create(validated_data)
