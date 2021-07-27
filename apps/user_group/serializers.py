from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin
from user_group.models import UserGroup, GroupMembership
from user_resource.serializers import UserResourceSerializer


class SimpleUserGroupSerializer(RemoveNullFieldsMixin,
                                serializers.ModelSerializer):
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

    class Meta:
        model = UserGroup
        fields = ('id', 'title', 'description', 'display_picture', 'role',
                  'memberships', 'global_crisis_monitoring',
                  'custom_project_fields', 'created_at', 'modified_at',
                  'created_by', 'modified_by'
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
