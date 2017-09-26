from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models
from user_resource.models import UserResource
from geo.models import Region
from user_group.models import UserGroup


class Project(UserResource):
    """
    Project model
    """

    title = models.CharField(max_length=255)
    members = models.ManyToManyField(User, blank=True,
                                     through='ProjectMembership')
    regions = models.ManyToManyField(Region, blank=True)
    user_groups = models.ManyToManyField(UserGroup, blank=True)
    data = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return self.title

    @staticmethod
    def get_for(user):
        """
        Project can be accessed only if
        * user is member of project
        * user is member of a group in the project
        """
        return Project.objects.filter(
            models.Q(members=user) |
            models.Q(user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self in Project.get_for(user)

    def can_modify(self, user):
        return ProjectMembership.objects.filter(
            project=self,
            member=user,
            role='admin',
        ).count() > 0


class ProjectMembership(models.Model):
    """
    Project-Member relationship attributes
    """

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

    @staticmethod
    def get_for(user):
        """
        Project (and it's membership) can be accessed only if
        * user is member of project
        * user is member of a group in the project
        """
        return ProjectMembership.objects.filter(
            models.Q(project__members=user) |
            models.Q(project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self.project.can_get(user)

    def can_modify(self, user):
        return self.project.can_modify(user)
