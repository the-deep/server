from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, transaction
from project.models import Project
from user_resource.models import UserResource
from gallery.models import File


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

    # Type of lead source
    TEXT = 'text'
    DISK = 'disk'
    WEBSITE = 'website'
    DROPBOX = 'dropbox'
    GOOGLE_DRIVE = 'google-drive'
    UNKNOWN = 'unknown'

    SOURCE_TYPES = (
        (TEXT, 'Text'),
        (DISK, 'Disk'),
        (WEBSITE, 'Website'),
        (DROPBOX, 'Dropbox'),
        (GOOGLE_DRIVE, 'Google Drive'),
        (UNKNOWN, 'Unknown'),
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
    url = models.CharField(max_length=255, blank=True)
    website = models.CharField(max_length=255, blank=True)

    attachment = models.ForeignKey(File,
                                   default=None, null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.title)

    # Lead preview is invalid upon save
    # Retrigger extraction
    def save(self, *args, **kwargs):
        super(Lead, self).save(*args, **kwargs)
        from lead.tasks import extract_from_lead
        LeadPreview.objects.filter(lead=self).delete()
        LeadPreviewImage.objects.filter(lead=self).delete()

        if not settings.TESTING:
            transaction.on_commit(lambda: extract_from_lead.delay(self.id))

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
