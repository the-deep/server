from django.contrib.auth.models import User
from django.db import models

from user_resource.models import UserResource


class UserGroup(UserResource):
    """
    User group model
    """
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    display_picture = models.ForeignKey(
        'gallery.File',
        on_delete=models.SET_NULL,
        null=True, blank=True, default=None,
    )
    members = models.ManyToManyField(
        User, blank=True,
        through_fields=('group', 'member'),
        through='GroupMembership',
    )
    global_crisis_monitoring = models.BooleanField(default=False)

    custom_project_fields = models.JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return self.title

    @staticmethod
    def get_for(user):
        return UserGroup.objects.all()

    @classmethod
    def get_for_member(cls, user, exclude=False):
        if exclude:
            return cls.objects.exclude(members=user).distinct()
        return cls.objects.filter(members=user).distinct()

    @staticmethod
    def get_modifiable_for(user):
        return UserGroup.objects.filter(
            groupmembership__in=GroupMembership.objects.filter(
                member=user,
                role=GroupMembership.Role.ADMIN,
            )
        ).distinct()

    def can_get(self, user):
        return True

    def is_member(self, user):
        return self in UserGroup.get_for_member(user)

    def can_delete(self, user):
        return self.created_by == user

    def can_modify(self, user):
        return GroupMembership.objects.filter(
            group=self,
            member=user,
            role=GroupMembership.Role.ADMIN,
        ).exists()

    def add_member(self, user, role=None, added_by=None):
        _role = role or GroupMembership.Role.NORMAL
        return GroupMembership.objects.create(
            member=user,
            role=_role,
            group=self,
            added_by=added_by or user,
        )


class GroupMembership(models.Model):
    """
    User group-Member relationship attributes
    """
    class Role(models.TextChoices):
        NORMAL = 'normal', 'Normal'
        ADMIN = 'admin', 'Admin'

    member = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)
    role = models.CharField(max_length=96, choices=Role.choices, default=Role.NORMAL)
    joined_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        null=True, blank=True, default=None,
        related_name='added_group_memberships',
    )

    def __str__(self):
        return '{} @ {}'.format(str(self.member),
                                self.group.title)

    class Meta:
        unique_together = ('member', 'group')

    @staticmethod
    def get_for(user):
        return GroupMembership.objects.all()

    def can_get(self, user):
        return self.group.can_get(user)

    def can_modify(self, user):
        return self.group.can_modify(user)

    @staticmethod
    def get_member_for_user_group(user_group):
        return GroupMembership.objects.filter(
            group=user_group
        ).distinct()
