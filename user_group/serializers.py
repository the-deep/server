from rest_framework import serializers
from user_group.models import UserGroup, GroupMembership


class UserGroupSerializer(serializers.ModelSerializer):
    memberships = serializers.SerializerMethodField()

    class Meta:
        model = UserGroup
        fields = ('id', 'title', 'display_picture',
                  'memberships',
                  'members', 'global_crisis_monitoring')

    def create(self, validated_data):
        user_group = super(UserGroupSerializer, self).create(validated_data)
        GroupMembership.objects.create(
            group=user_group,
            member=self.context['request'].user,
            role='admin'
        )
        return user_group

    def get_memberships(self, group):
        return GroupMembership.objects.filter(group=group)\
            .distinct().values_list('id', flat=True)


class GroupMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMembership
        fields = ('id', 'member', 'group', 'role', 'joined_at')

    # Validations
    def validate_group(self, group):
        if not group.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid user group')
        return group
