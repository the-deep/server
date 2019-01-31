from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, transaction

from project.models import Project
from project.mixins import ProjectEntityMixin
from user_resource.models import UserResource
from tabular.models import Book
from gallery.models import File


class LeadGroup(UserResource):
    title = models.CharField(max_length=255, blank=True)
    project = models.ForeignKey(Project)

    def __str__(self):
        return self.title

    @staticmethod
    def get_for(user):
        return LeadGroup.objects.filter(
            models.Q(project__members=user) |
            models.Q(project__user_groups__members=user)
        ).annotate(
            no_of_leads=models.Count('lead', distinct=True)
        ).distinct()

    def can_get(self, user):
        return self.project.is_member(user)

    def can_modify(self, user):
        return self.project.is_member(user)


class Lead(UserResource, ProjectEntityMixin):
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

    # Type of lead source
    TEXT = 'text'
    DISK = 'disk'
    WEBSITE = 'website'
    DROPBOX = 'dropbox'
    GOOGLE_DRIVE = 'google-drive'
    RSS = 'rss'
    WEB_API = 'api'
    UNKNOWN = 'unknown'

    SOURCE_TYPES = (
        (TEXT, 'Text'),
        (DISK, 'Disk'),
        (WEBSITE, 'Website'),
        (DROPBOX, 'Dropbox'),
        (GOOGLE_DRIVE, 'Google Drive'),

        (RSS, 'RSS Feed'),
        (WEB_API, 'Web API'),
        (UNKNOWN, 'Unknown'),
    )

    lead_group = models.ForeignKey(
        LeadGroup,
        on_delete=models.SET_NULL,
        null=True, blank=True, default=None,
    )

    project = models.ForeignKey(Project)
    title = models.CharField(max_length=255)
    source = models.CharField(max_length=255, blank=True)
    source_type = models.CharField(max_length=30,
                                   choices=SOURCE_TYPES,
                                   default=UNKNOWN)

    confidentiality = models.CharField(max_length=30,
                                       choices=CONFIDENTIALITIES,
                                       default=UNPROTECTED)
    status = models.CharField(max_length=30,
                              choices=STATUSES,
                              default=PENDING)

    assignee = models.ManyToManyField(User, blank=True)
    published_on = models.DateField(default=None, null=True, blank=True)

    text = models.TextField(blank=True)
    url = models.TextField(blank=True)
    website = models.CharField(max_length=255, blank=True)

    attachment = models.ForeignKey(File, on_delete=models.SET_NULL,
                                   default=None, null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.title)

    # Lead preview is invalid while saving url/text/attachment
    # Retrigger extraction at such cases

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.pk:
            self.__initial = self.get_dict()
        else:
            self.__initial = None

    def get_dict(self):
        return {
            'text': self.text,
            'url': self.url,
            'attachment': self.attachment,
        }

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from lead.tasks import extract_from_lead

        if not settings.TESTING:
            d1 = self.__initial
            d2 = self.get_dict()
            if not d1 or d1.get('text') != d2.get('text') or \
                    d1.get('url') != d2.get('url') or \
                    d1.get('attachment') != d2.get('attachment'):
                transaction.on_commit(lambda: extract_from_lead.delay(self.id))

    @classmethod
    def get_for(cls, user):
        """
        Lead can only be accessed by users who have access to
        it's project
        """
        qs = super().get_for(user)
        return qs.annotate(
            no_of_entries=models.Count('entry', distinct=True)
        )

    def get_assignee(self):
        return self.assignee.first()


class LeadPreview(models.Model):
    lead = models.OneToOneField(Lead)
    text_extract = models.TextField(blank=True)

    classified_doc_id = models.IntegerField(default=None,
                                            null=True, blank=True)

    def __str__(self):
        return 'Text extracted for {}'.format(self.lead)


class LeadPreviewImage(models.Model):
    lead = models.ForeignKey(Lead, related_name='images')
    file = models.FileField(upload_to='lead-preview/')

    def __str__(self):
        return 'Image extracted for {}'.format(self.lead)
