from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models
from user_resource.models import UserResource
from geo.models import Region
from user_group.models import UserGroup


class Project(UserResource):
    title = models.CharField(max_length=255)
    members = models.ManyToManyField(User, blank=True,
                                     through='ProjectMembership')
    regions = models.ManyToManyField(Region, blank=True)
    user_groups = models.ManyToManyField(UserGroup, blank=True)
    data = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return self.title


class ProjectMembership(models.Model):

    ROLES = [
        ('normal', 'Normal'),
        ('admin', 'Admin'),
    ]

    member = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, choices=ROLES,
                            default='normal')
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{} @ {}'.format(str(self.member),
                                self.project.title)
