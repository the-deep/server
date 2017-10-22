from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from user_group.models import UserGroup, GroupMembership


class GroupMembershipSerializer(DynamicFieldsMixin,
                                serializers.ModelSerializer):
    member_name = serializers.SerializerMethodField()

    class Meta:
        model = GroupMembership
        fields = ('id', 'member', 'member_name',
                  'group', 'role', 'joined_at')

    def get_member_name(self, membership):
        return membership.member.profile.get_display_name()

    # Validations
    def validate_group(self, group):
        if not group.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid user group')
        return group


class UserGroupSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    memberships = GroupMembershipSerializer(
        source='groupmembership_set',
        many=True, read_only=True
    )

    class Meta:
        model = UserGroup
        fields = ('id', 'title', 'display_picture',
                  'memberships', 'global_crisis_monitoring')

    def create(self, validated_data):
        user_group = super(UserGroupSerializer, self).create(validated_data)
        GroupMembership.objects.create(
            group=user_group,
            member=self.context['request'].user,
            role='admin'
        )
        return user_group
