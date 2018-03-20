from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models
from user_resource.models import UserResource
from geo.models import Region
from user_group.models import UserGroup
from analysis_framework.models import AnalysisFramework
from category_editor.models import CategoryEditor


class Project(UserResource):
    """
    Project model
    """

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    start_date = models.DateField(default=None, null=True, blank=True)
    end_date = models.DateField(default=None, null=True, blank=True)

    members = models.ManyToManyField(User, blank=True,
                                     through='ProjectMembership')
    regions = models.ManyToManyField(Region, blank=True)
    user_groups = models.ManyToManyField(UserGroup, blank=True)
    analysis_framework = models.ForeignKey(AnalysisFramework, blank=True,
                                           default=None, null=True,
                                           on_delete=models.SET_NULL)
    category_editor = models.ForeignKey(CategoryEditor, blank=True,
                                        default=None, null=True,
                                        on_delete=models.SET_NULL)
    assessment_template = models.ForeignKey('ary.AssessmentTemplate',
                                            blank=True, default=None,
                                            null=True,
                                            on_delete=models.SET_NULL)
    data = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return self.title

    # def save(self, *args, **kwargs):
    #     # If analysis framework not set, set one automatically
    #     if not self.analysis_framework:
    #         analysis_framework = AnalysisFramework(title=self.title)
    #         analysis_framework.save()
    #         self.analysis_framework = analysis_framework
    #     super(UserResource, self).save(*args, **kwargs)

    @staticmethod
    def get_for(user):
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
        ).exists()


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

    class Meta:
        unique_together = ('member', 'project')

    @staticmethod
    def get_for(user):
        return ProjectMembership.objects.all()

    def can_get(self, user):
        return True

    def can_modify(self, user):
        return self.project.can_modify(user)
