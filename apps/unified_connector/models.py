from django.db import models
from django.contrib.postgres.fields import ArrayField
from user_resource.models import UserResource

from lead.models import Lead
from organization.models import Organization
from project.models import Project


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


class ConnectorSource(UserResource):
    class Source(models.TextChoices):
        ATOM_FEED = 'atom-feed', 'Atom Feed'
        RELIEF_WEB = 'relief-web', 'Relifweb'
        RSS_FEED = 'rss-feed', 'RSS Feed'
        UNHCR = 'unhcr-portal', 'UNHCR Portal'

    title = models.CharField(max_length=255)
    unified_connector = models.ForeignKey(UnifiedConnector, on_delete=models.CASCADE, related_name='sources')
    source = models.CharField(max_length=20, choices=Source.choices)
    params = models.JSONField(default=dict)
    client_id = None

    class Meta:
        unique_together = ('unified_connector', 'source',)

    def __str__(self):
        return self.title


class ConnectorLead(models.Model):
    url = models.TextField()
    title = models.CharField(max_length=255)
    published_on = models.DateField(default=None, null=True, blank=True)
    source_raw = models.CharField(max_length=255, blank=True)
    authors_raw = ArrayField(models.CharField(max_length=100), default=list)
    authors = models.ManyToManyField(Organization, blank=True, related_name='+')
    source = models.ForeignKey(Organization, related_name='+', on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    extraction_status = models.SmallIntegerField(
        choices=Lead.ExtractionStatus.choices, default=Lead.ExtractionStatus.PENDING
    )


class ConnectorSourceLead(models.Model):  # ConnectorSource's Leads
    source = models.ForeignKey(ConnectorSource, on_delete=models.CASCADE)
    connector_lead = models.ForeignKey(ConnectorLead, on_delete=models.CASCADE)
    blocked = models.BooleanField(default=False)
    already_added = models.BooleanField(default=False)
