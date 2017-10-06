from django.contrib.auth.models import User
from django.db import models
from project.models import Project
from user_resource.models import UserResource


class Lead(UserResource):
    """
    Lead model

    Represents either text, url or file attachment along with
    some basic attributes such as title, condidentiality, date published,
    source etc.

    A lead belongs to one project.
    """

    # Confidentiality choices
    UNPROTECTED = 'unprotected'
    PROTECTED = 'protected'
    RESTRICTED = 'restricted'
    CONFIDENTIAL = 'confidential'

    CONFIDENTIALITIES = (
        (UNPROTECTED, 'Unprotected'),
        (PROTECTED, 'Protected'),
        (RESTRICTED, 'Restricted'),
        (CONFIDENTIAL, 'Confidential'),
    )

    # Status of a lead that can be pending, processed or deleted.
    PENDING = 'pending'
    PROCESSED = 'processed'

    STATUSES = (
        (PENDING, 'Pending'),
        (PROCESSED, 'Processed'),
    )

    project = models.ForeignKey(Project)
    title = models.CharField(max_length=255)
    source = models.CharField(max_length=255, blank=True)

    confidentiality = models.CharField(max_length=30,
                                       choices=CONFIDENTIALITIES,
                                       default=UNPROTECTED)
    status = models.CharField(max_length=30,
                              choices=STATUSES,
                              default=PENDING)

    assignee = models.ManyToManyField(User, blank=True)
    published_on = models.DateField(default=None, null=True, blank=True)

    text = models.TextField(blank=True)
    url = models.CharField(max_length=255, blank=True)
    website = models.CharField(max_length=255, blank=True)

    attachment = models.FileField(upload_to='lead-attachments/%Y/%m/',
                                  default=None, null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.title)

    @staticmethod
    def get_for(user):
        """
        Lead can only be accessed by users who have access to
        it's project
        """
        return Lead.objects.filter(
            models.Q(project__members=user) |
            models.Q(project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self.project.can_get(user)

    def can_modify(self, user):
        # Not project.can_modify as only admin of projects
        # can modify a project but anybody who can view project
        # can modify a lead in that project
        return self.project.can_get(user)
