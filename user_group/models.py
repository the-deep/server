from django.contrib.auth.models import User
from django.db import models


class UserGroup(models.Model):
    title = models.CharField(max_length=255, blank=True)
    display_picture = models.FileField(upload_to='group_dp/',
                                       null=True, blank=True, default=None)
    members = models.ManyToManyField(User, blank=True,
                                     through='GroupMembership')
    global_crisis_monitoring = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class GroupMembership(models.Model):
    ROLES = [
        ('normal', 'Normal'),
        ('admin', 'Admin'),
    ]

    member = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, choices=ROLES,
                            default='normal')
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{} @ {}'.format(str(self.member),
                                self.group.title)
