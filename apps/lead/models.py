from django.contrib.contenttypes.fields import GenericRelation
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, transaction

from project.models import Project
from project.permissions import PROJECT_PERMISSIONS
from project.mixins import ProjectEntityMixin
from notification.models import Assignment
from organization.models import Organization
from user_resource.models import UserResource
from gallery.models import File


class LeadGroup(UserResource):
    title = models.CharField(max_length=255, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    @staticmethod
    def get_for_project(project):
        return LeadGroup.objects.filter(project=project)

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

    class Confidentiality(models.TextChoices):
        UNPROTECTED = 'unprotected', 'Unprotected'
        CONFIDENTIAL = 'confidential', 'Confidential'

    class Status(models.TextChoices):
        # TODO: Update enum value
        NOT_TAGGED = 'pending', 'Not Tagged'
        IN_PROGRESS = 'processed', 'In progress'
        TAGGED = 'validated', 'Tagged'

    class Priority(models.IntegerChoices):
        HIGH = 300, 'High'
        MEDIUM = 200, 'Medium'
        LOW = 100, 'Low'

    class SourceType(models.TextChoices):
        TEXT = 'text', 'Text'
        DISK = 'disk', 'Disk'
        WEBSITE = 'website', 'Website'
        DROPBOX = 'dropbox', 'Dropbox'
        GOOGLE_DRIVE = 'google-drive', 'Google Drive'

        RSS = 'rss', 'RSS Feed'
        EMM = 'emm', 'EMM'
        WEB_API = 'api', 'Web API'
        UNKNOWN = 'unknown', 'Unknown'

    class ExtractionStatus(models.IntegerChoices):
        PENDING = 0, 'Pending'
        STARTED = 1, 'Started'
        SUCCESS = 2, 'Success'
        FAILED = 3, 'Failed'

    lead_group = models.ForeignKey(
        LeadGroup,
        on_delete=models.SET_NULL,
        null=True, blank=True, default=None,
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)

    authors = models.ManyToManyField(Organization, blank=True)
    # TODO: Remove (Legacy), Make sure to copy author to authors if authors is empty
    author = models.ForeignKey(
        Organization, verbose_name='author (legacy)', related_name='leads_by_author',
        on_delete=models.SET_NULL, null=True, blank=True, default=None,
    )
    source = models.ForeignKey(
        Organization, related_name='leads_by_source',
        on_delete=models.SET_NULL, null=True, blank=True, default=None,
    )

    # Legacy Data (Remove after migrating all data)
    author_raw = models.CharField(max_length=255, blank=True)
    source_raw = models.CharField(max_length=255, blank=True)

    source_type = models.CharField(max_length=30, choices=SourceType.choices, default=SourceType.UNKNOWN)
    priority = models.IntegerField(choices=Priority.choices, default=Priority.LOW)
    confidentiality = models.CharField(max_length=30, choices=Confidentiality.choices, default=Confidentiality.UNPROTECTED)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.NOT_TAGGED)

    assignee = models.ManyToManyField(User, blank=True)
    published_on = models.DateField(default=None, null=True, blank=True)

    text = models.TextField(blank=True)
    url = models.TextField(blank=True)
    website = models.CharField(max_length=255, blank=True)
    extraction_status = models.SmallIntegerField(
        choices=ExtractionStatus.choices, default=ExtractionStatus.PENDING)

    attachment = models.ForeignKey(
        File, on_delete=models.SET_NULL, default=None, null=True, blank=True,
    )

    emm_entities = models.ManyToManyField('EMMEntity', blank=True)
    assignments = GenericRelation(Assignment, related_query_name='lead')
    is_assessment_lead = models.BooleanField(default=False)

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
            'attachment_id': self.attachment_id,
        }

    def update_extraction_status(self, new_status, commit=True):
        self.extraction_status = new_status
        if commit:
            self.save(update_fields=('extraction_status',))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        update_fields = kwargs.get('update_fields')

        initial_fields = ['text', 'attachment', 'attachment_id', 'url']
        if (
            not settings.TESTING and (
                self.id is None or
                update_fields is None or
                any(x in update_fields for x in initial_fields)
            )
        ):
            from lead.tasks import extract_from_lead

            d1 = self.__initial
            d2 = self.get_dict()
            if not d1 or d1.get('text') != d2.get('text') or \
                    d1.get('url') != d2.get('url') or \
                    d1.get('attachment_id') != d2.get('attachment_id'):
                transaction.on_commit(lambda: extract_from_lead.delay(self.id))

    @classmethod
    def get_for(cls, user, filters=None):
        """
        Lead can only be accessed by users who have access to
        it's project along with required permissions
        param: filters: filters that need to be applied into queryset
        """
        from entry.filter_set import get_filtered_entries

        filters = filters or dict()

        view_unprotected_perm_value = PROJECT_PERMISSIONS.lead.view_only_unprotected
        view_perm_value = PROJECT_PERMISSIONS.lead.view

        # NOTE: This is quite complicated because user can have two view roles:
        # view all or view only unprotected, both of which return different results

        qs = cls.objects.filter(
            # First filter if user is member
            project__projectmembership__member=user,
        ).annotate(
            # Get permission value for view_only_unprotected permission
            view_unprotected=models.F(
                'project__projectmembership__role__lead_permissions'
            ).bitand(view_unprotected_perm_value),
            # Get permission value for view permission
            view_all=models.F(
                'project__projectmembership__role__lead_permissions'
            ).bitand(view_perm_value)
        ).filter(
            # If view only unprotected, filter leads with confidentiality not confidential
            (
                models.Q(view_unprotected=view_unprotected_perm_value) &
                ~models.Q(confidentiality=Lead.Confidentiality.CONFIDENTIAL)
            ) |
            # Or, return nothing if view_all is not present
            models.Q(view_all=view_perm_value)
        )
        # filter entries
        entries_filter_data = filters.get('entries_filter_data', {})
        original_filter = {**entries_filter_data}
        original_filter.pop('project', None)
        entries_filter_data['from_subquery'] = True

        return qs.annotate(
            entries_count=models.Count('entry', distinct=True),
            assessment_id=models.F('assessment'),
            controlled_entries_count=models.Count('entry', filter=models.Q(entry__controlled=True)),
            filtered_entries_count=models.functions.Coalesce(
                models.Subquery(
                    get_filtered_entries(user, entries_filter_data).filter(
                        lead=models.OuterRef('pk')
                    ).values('lead').order_by().annotate(
                        count=models.Count('id')
                    ).values('count')[:1], output_field=models.IntegerField()
                ), 0
            ) if original_filter else models.F('entries_count'),
            controlled_filtered_entries_count=models.functions.Coalesce(
                models.Subquery(
                    get_filtered_entries(user, entries_filter_data).filter(
                        lead=models.OuterRef('pk'),
                        controlled=True
                    ).values('lead').order_by().annotate(
                        count=models.Count('id')
                    ).values('count')[:1], output_field=models.IntegerField()
                ), 0
            ) if original_filter else models.F('controlled_entries_count'),
        )

    def get_assignee(self):
        # To be used by prefetch_related (Also, there is only one assignee)
        assignees = self.assignee.all()
        if assignees:
            return assignees[0]

    def get_source_display(self):
        if self.source:
            return self.source.data.title
        return self.source_raw

    def get_authors_display(self):
        authors = self.authors.all()
        if authors:
            return ','.join([
                author.data.title for author in authors
            ])
        elif self.author:
            # TODO: Remove (Legacy)
            return self.author and self.author.data.title
        return self.author_raw

    def get_authoring_organizations_type_display(self):
        authors = self.authors.all()
        if authors:
            return ','.join(set([
                author.get_organization_type_display() for author in authors if author.data.organization_type
            ]))
        elif self.author:
            return self.author.data.organization_type and self.author.data.organization_type.title
        return

    @classmethod
    def get_associated_entities(cls, project_id, lead_ids):
        """
        Used for pre-check before deletion
        """
        from entry.models import Entry
        from ary.models import Assessment
        return {
            'entries': Entry.objects.filter(lead__in=lead_ids, lead__project_id=project_id).count(),
            'assessments': Assessment.objects.filter(lead__project_id=project_id, lead__in=lead_ids).count(),
        }

    @classmethod
    def get_emm_summary(cls, lead_qs):
        # Aggregate emm data
        emm_entities = EMMEntity.objects\
            .filter(lead__in=lead_qs).values('name')\
            .annotate(total_count=models.Count('name'))\
            .order_by('-total_count').values('name', 'total_count')
        emm_triggers = LeadEMMTrigger.objects\
            .filter(lead__in=lead_qs).values('emm_keyword', 'emm_risk_factor')\
            .annotate(total_count=models.Sum('count'))\
            .order_by('-total_count').values('emm_keyword', 'emm_risk_factor', 'total_count')
        return {
            'emm_entities': emm_entities,
            'emm_triggers': emm_triggers,
        }


class LeadPreview(models.Model):
    class ClassificationStatus(models.TextChoices):
        NONE = 'none', 'None'  # For leads which are not texts
        INITIATED = 'initiated', 'Initiated'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'  # Somehow Failed due to connection error
        ERRORED = 'errored', 'Errored'  # If errored, no point in retrying

    lead = models.OneToOneField(Lead, on_delete=models.CASCADE)
    text_extract = models.TextField(blank=True)

    thumbnail = models.ImageField(
        upload_to='lead-thumbnail/',
        default=None, null=True, blank=True,
        height_field='thumbnail_height',
        width_field='thumbnail_width'
    )
    thumbnail_height = models.IntegerField(default=None, null=True, blank=True)
    thumbnail_width = models.IntegerField(default=None, null=True, blank=True)
    word_count = models.IntegerField(default=None, null=True, blank=True)
    page_count = models.IntegerField(default=None, null=True, blank=True)

    classified_doc_id = models.IntegerField(default=None,
                                            null=True, blank=True)
    classification_status = models.CharField(
        max_length=20,
        choices=ClassificationStatus.choices,
        default=ClassificationStatus.NONE,
    )

    def __str__(self):
        return 'Text extracted for {}'.format(self.lead)


class LeadPreviewImage(models.Model):
    """
    NOTE: File can be only used by gallery (when attached to a entry)
    """
    lead = models.ForeignKey(
        Lead, related_name='images', on_delete=models.CASCADE,
    )
    file = models.FileField(upload_to='lead-preview/')

    def __str__(self):
        return 'Image extracted for {}'.format(self.lead)

    def clone_as_deep_file(self, user):
        """
        Generates a gallery/models.py::File copy
        """
        file = File.objects.create(
            title=self.file.name,
            created_by=user,
            modified_by=user,
        )
        file.file.save(self.file.name, self.file)
        file.projects.add(self.lead.project)
        return file


class LeadEMMTrigger(models.Model):
    lead = models.ForeignKey(Lead, related_name='emm_triggers', on_delete=models.CASCADE)
    emm_keyword = models.CharField(max_length=100)
    emm_risk_factor = models.CharField(max_length=100)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('-count',)


class EMMEntity(models.Model):
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name
