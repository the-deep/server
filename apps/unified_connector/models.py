from typing import Union

from django.db import models
from django.db import transaction
from user_resource.models import UserResource

from lead.models import Lead
from organization.models import Organization
from project.models import Project, ProjectStats
from .sources import (
    atom_feed,
    rss_feed,
    unhcr_portal,
    relief_web,
    humanitarian_response,
    pdna,
    emm,
    kobo,
)


class ConnectorLead(models.Model):
    class ExtractionStatus(models.IntegerChoices):
        PENDING = 0, 'Pending'
        RETRYING = 1, 'Retrying'
        STARTED = 2, 'Started'
        SUCCESS = 3, 'Success'
        FAILED = 4, 'Failed'

    id: Union[int, None]
    url = models.TextField(unique=True)
    website = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255)
    published_on = models.DateField(default=None, null=True, blank=True)
    source_raw = models.CharField(max_length=255, blank=True)
    author_raw = models.CharField(max_length=255, blank=True)
    authors = models.ManyToManyField(Organization, blank=True, related_name='+')
    source = models.ForeignKey(Organization, related_name='+', on_delete=models.SET_NULL, null=True, blank=True)

    # Extracted data
    simplified_text = models.TextField(blank=True)
    word_count = models.IntegerField(blank=True, null=True)
    page_count = models.IntegerField(blank=True, null=True)
    text_extraction_id = models.UUIDField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    extraction_status = models.SmallIntegerField(
        choices=ExtractionStatus.choices, default=ExtractionStatus.PENDING
    )

    def __init__(self, *args, **kwargs):
        self.preview_images: models.QuerySet[ConnectorLeadPreviewAttachment]
        super().__init__(*args, **kwargs)

    @classmethod
    def get_or_create_from_lead(cls, lead: Lead):
        instance, created = cls.objects.get_or_create(
            url=lead.url,
            defaults=dict(
                title=lead.title,
                published_on=lead.published_on,
                source_raw=lead.source_raw or '',
                author_raw=lead.author_raw or '',
                source=lead.source,
            ),
        )
        if not created:
            return instance, False
        # NOTE: Custom attributes from connector
        authors = getattr(lead, '_authors', None)
        if authors:
            instance.authors.set(authors)
        return instance, True

    def update_extraction_status(self, new_status, commit=True):
        self.extraction_status = new_status
        if commit:
            self.save(update_fields=('extraction_status',))


class ConnectorLeadPreviewAttachment(models.Model):
    class ConnectorAttachmentFileType(models.IntegerChoices):
        XLSX = 1, 'XLSX'
        IMAGE = 2, 'Image'

    connector_lead = models.ForeignKey(ConnectorLead, on_delete=models.CASCADE, related_name='preview_images')
    order = models.IntegerField(default=0)
    page_number = models.IntegerField(default=0)
    type = models.PositiveSmallIntegerField(
        choices=ConnectorAttachmentFileType.choices,
        default=ConnectorAttachmentFileType.XLSX
    )
    file = models.FileField(upload_to='connector-lead/attachments/')
    file_preview = models.FileField(upload_to='connector-lead/attachments-preview/')


class UnifiedConnector(UserResource):
    """
    Unified Connector: Contains source level connector
    """
    title = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    client_id = None

    def __str__(self):
        return self.title

    def can_delete(self, _):
        # Nothing on model level. Use permission on mutation
        return True


class ConnectorSource(UserResource):
    class Source(models.TextChoices):
        ATOM_FEED = 'atom-feed', 'Atom Feed'
        RELIEF_WEB = 'relief-web', 'Relifweb'
        RSS_FEED = 'rss-feed', 'RSS Feed'
        UNHCR = 'unhcr-portal', 'UNHCR Portal'
        HUMANITARIAN_RESP = 'humanitarian-resp', 'Humanitarian Response'
        PDNA = 'pdna', 'Post Disaster Needs Assessments'
        EMM = 'emm', 'European Media Monitor'
        KOBO = 'kobo', 'KoboToolbox'

    class Status(models.IntegerChoices):
        PENDING = 0, 'Pending'
        PROCESSING = 1, 'Processing'
        SUCCESS = 2, 'success'
        FAILURE = 3, 'failure'

    SOURCE_FETCHER_MAP = {
        Source.ATOM_FEED: atom_feed.AtomFeed,
        Source.RELIEF_WEB: relief_web.ReliefWeb,
        Source.RSS_FEED: rss_feed.RssFeed,
        Source.UNHCR: unhcr_portal.UNHCRPortal,
        Source.HUMANITARIAN_RESP: humanitarian_response.HumanitarianResponse,
        Source.PDNA: pdna.PDNA,
        Source.EMM: emm.EMM,
        Source.KOBO: kobo.Kobo,
    }

    title = models.CharField(max_length=255)
    unified_connector = models.ForeignKey(UnifiedConnector, on_delete=models.CASCADE, related_name='sources')
    source = models.CharField(max_length=20, choices=Source.choices)
    params = models.JSONField(default=dict)
    client_id = None

    leads = models.ManyToManyField(
        ConnectorLead, blank=True,
        through_fields=('source', 'connector_lead'),
        through='ConnectorSourceLead',
    )
    last_fetched_at = models.DateTimeField(blank=True, null=True)
    stats = models.JSONField(default=dict)  # {published_dates: ['date': <>, 'count': <>]}
    status = models.SmallIntegerField(choices=Status.choices, default=Status.PENDING)
    # Execution time
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_params = self.params

    @property
    def source_fetcher(self):
        return self.SOURCE_FETCHER_MAP[self.source]

    def generate_stats(self, commit=True):
        threshold = ProjectStats.get_activity_timeframe()
        self.stats = {
            'published_dates': [
                {
                    'date': str(date),
                    'count': count,
                } for count, date in self.leads.filter(
                    published_on__isnull=False,
                    published_on__gte=threshold,
                ).order_by().values('published_on').annotate(
                    count=models.Count('*'),
                ).values_list('count', models.F('published_on'))
            ],
            'leads_count': self.leads.count(),
        }
        if commit:
            self.save()

    def add_lead(self, lead, **kwargs):
        already_added = self.unified_connector.project.lead_set.filter(url=lead.url).exists()
        return ConnectorSourceLead.objects.create(
            connector_lead=lead,
            source=self,
            already_added=already_added,
            **kwargs,
        )

    def save(self, *args, **kwargs):
        params_changed = (
            self.old_params != self.params and
            ('params' in kwargs['update_fields'] if 'update_fields' in kwargs else True)
        )
        if params_changed:
            # Reset attributes if params are changed
            transaction.on_commit(lambda: self.leads.clear())
            self.last_fetched_at = None
            self.stats = {}
            self.status = ConnectorSource.Status.PENDING
            if 'update_fields' in kwargs:
                kwargs['update_fields'] = list(set([
                    'stats',
                    'status',
                    'last_fetched_at',
                    *kwargs['update_fields']
                ]))
        super().save(*args, **kwargs)
        self.old_params = self.params


class ConnectorSourceLead(models.Model):  # ConnectorSource's Leads
    source = models.ForeignKey(ConnectorSource, on_delete=models.CASCADE, related_name='source_leads')
    connector_lead = models.ForeignKey(ConnectorLead, on_delete=models.CASCADE)
    blocked = models.BooleanField(default=False)
    already_added = models.BooleanField(default=False)

    @classmethod
    def update_aleady_added_using_lead(cls, lead, added=True):
        return cls.objects.filter(
            connector_lead=lead.connector_lead,
            source__unified_connector__project=lead.project,
        ).update(already_added=added)

