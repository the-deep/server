from django.contrib.postgres.fields import JSONField
from django.db import models, transaction
from django.db.models.functions import Cast
from django.contrib.postgres.fields.jsonb import KeyTransform, KeyTextTransform

from utils.common import is_valid_regex

from user_resource.models import UserResource
from project.models import Project
from user.models import User

from .sources.store import source_store


class ConnectorSource(models.Model):
    STATUS_BROKEN = 'broken'
    STATUS_WORKING = 'working'

    STATUS_CHOICES = (
        (STATUS_BROKEN, 'Broken'),
        (STATUS_WORKING, 'Working'),
    )

    key = models.CharField(max_length=100, primary_key=True)
    title = models.CharField(max_length=100)
    logo = models.FileField(upload_to='connector-logo/', max_length=255, null=True, blank=True, default=None)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=STATUS_WORKING,
    )
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Connector(UserResource):
    title = models.CharField(max_length=255)
    source = models.ForeignKey(
        ConnectorSource,
        null=True,
        on_delete=models.CASCADE,
    )
    params = JSONField(default=None, blank=True, null=True)

    users = models.ManyToManyField(User, blank=True,
                                   through='ConnectorUser')
    projects = models.ManyToManyField(Project, blank=True,
                                      through='ConnectorProject')

    def __str__(self):
        return self.title

    @staticmethod
    def get_for(user):
        return Connector.objects.filter(
            models.Q(users=user) |
            models.Q(projects__members=user) |
            models.Q(projects__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self in Connector.get_for(user)

    def can_modify(self, user):
        return ConnectorUser.objects.filter(
            connector=self,
            user=user,
            role='admin',
        ).exists()

    def add_member(self, user, role='normal'):
        return ConnectorUser.objects.create(
            user=user,
            role=role,
            connector=self,
        )


class ConnectorUser(models.Model):
    """
    Connector-User relationship attributes
    """

    ROLES = (
        ('normal', 'Normal'),
        ('admin', 'Admin'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    connector = models.ForeignKey(Connector, on_delete=models.CASCADE)
    role = models.CharField(max_length=96, choices=ROLES,
                            default='normal')
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{} @ {}'.format(str(self.user), self.connector.title)

    class Meta:
        unique_together = ('user', 'connector')

    @staticmethod
    def get_for(user):
        return ConnectorUser.objects.all()

    def can_get(self, user):
        return True

    def can_modify(self, user):
        return self.connector.can_modify(user)


class ConnectorProject(models.Model):
    """
    Connector-Project relationship attributes
    """

    ROLES = (
        ('self', 'For self only'),
        ('global', 'For all members of project'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    connector = models.ForeignKey(Connector, on_delete=models.CASCADE)
    role = models.CharField(max_length=96, choices=ROLES,
                            default='self')
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{} @ {}'.format(str(self.project), self.connector.title)

    class Meta:
        unique_together = ('project', 'connector')

    @staticmethod
    def get_for(user):
        return ConnectorProject.objects.all()

    def can_get(self, user):
        return True

    def can_modify(self, user):
        return self.connector.can_modify(user)


EMM_SEPARATOR_DEFAULT = ';'
EMM_TRIGGER_REGEX_DEFAULT = r'(\((?P<risk_factor>[a-zA-Z ]+)\)){0,1}(?P<keyword>[a-zA-Z ]+)\[(?P<count>\d+)]'
EMM_ENTITY_TAG_DEFAULT = 'emm:entity'
EMM_TRIGGER_TAG_DEFAULT = 'category'
EMM_TRIGGER_ATTRIBUTE_DEFAULT = 'emm:trigger'


class EMMConfig(models.Model):
    trigger_separator = models.CharField(max_length=10, default=EMM_SEPARATOR_DEFAULT)
    trigger_regex = models.CharField(max_length=300, default=EMM_TRIGGER_REGEX_DEFAULT)
    entity_tag = models.CharField(max_length=100, default=EMM_ENTITY_TAG_DEFAULT)
    trigger_tag = models.CharField(max_length=50, default=EMM_TRIGGER_TAG_DEFAULT)
    trigger_attribute = models.CharField(max_length=50, default=EMM_TRIGGER_ATTRIBUTE_DEFAULT)

    def __str__(self):
        return f'{self.entity_tag}:{self.trigger_tag}:{self.trigger_attribute}'

    # Just Allow to have a single config
    def save(self, *args, **kwargs):
        self.pk = 1
        # Check if valid regex
        if not is_valid_regex(self.trigger_regex):
            raise Exception(f'{self.trigger_regex} is not a valid Regular Expression')
        super().save(*args, **kwargs)


# ------------------------------------- UNIFIED CONNECTOR -------------------------------------- #

class ConnectorLead(models.Model):
    """
    Leads collected from connectors.
    This is assigned to UnifiedConnectorSource using UnifiedConnectorSourceLead
    """
    class Status():
        SUCCESS = 'success'
        FAILURE = 'failure'

        CHOICES = [
            (SUCCESS, 'Success'),
            (FAILURE, 'Failure'),
        ]

    url = models.TextField(blank=True)
    status = models.CharField(max_length=30, blank=True, null=True, choices=Status.CHOICES)
    data = JSONField(default=dict, blank=True)  # NOTE: Extract data is copied in AWS dynamodb

    def __str__(self):
        return f'{self.get_status_display()}:{self.url}'


class UnifiedConnector(UserResource):
    """
    Unified Connector: Contains source level connector
    """
    title = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def can_modify(self, user):
        return self.project.can_modify(user)


class UnifiedConnectorSource(models.Model):
    """
    Source Connectors:
    - Source Type (Reliefweb, WorldFoodProgramme, etc)
    - Params: Contains parameters to fetch leads from selected source.
    - Stats (Number of leads by Year-Month)
    - Status
    """
    class Status():
        NOT_PROCESSED = 'not_processed'
        PROCESSING = 'processing'
        SUCCESS = 'success'
        FAILURE = 'failure'

        CHOICES = [
            (NOT_PROCESSED, 'Not Processed'),
            (PROCESSING, 'Processing'),
            (SUCCESS, 'Success'),
            (FAILURE, 'Failure'),
        ]

    source = models.ForeignKey(ConnectorSource, on_delete=models.CASCADE)
    connector = models.ForeignKey(UnifiedConnector, on_delete=models.CASCADE)
    params = JSONField(default=dict, blank=True)

    # Server Generated Attributes
    last_calculated_at = models.DateTimeField(blank=True, null=True)
    stats = JSONField(default=dict, blank=True)  # number of leads by Year-Month
    status = models.CharField(max_length=30, default=Status.NOT_PROCESSED, choices=Status.CHOICES)
    leads = models.ManyToManyField(
        ConnectorLead, blank=True,
        through_fields=('source', 'lead'),
        through='UnifiedConnectorSourceLead',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_params = self.params

    def __str__(self):
        return self.source_id

    def can_modify(self, user):
        return self.connector.can_modify(user)

    @classmethod
    def annotate_leads_count(cls, qs):
        return qs.annotate(
            total_leads=models.Count('leads', distinct=True),
            already_not_added_and_not_blocked_leads=models.Count(
                'unifiedconnectorsourcelead',
                filter=(
                    models.Q(unifiedconnectorsourcelead__already_added=False) &
                    models.Q(unifiedconnectorsourcelead__blocked=False)
                ),
                distinct=True,
            ),
        )

    @property
    def source_fetcher(self):
        return source_store[self.source_id]

    def add_lead(self, lead, **kwargs):
        already_added = self.connector.project.lead_set.filter(url=lead.url).exists()
        return UnifiedConnectorSourceLead.objects.create(
            lead=lead,
            source=self,
            already_added=already_added,
            **kwargs,
        )

    def generate_stats(self, commit=True):
        self.stats = {
            'published_dates': list(
                self.leads.filter(data__published_on__isnull=False).annotate(
                    published_date=Cast(
                        Cast(KeyTextTransform('published_on', 'data'), models.DateField()),
                        models.CharField()
                    )
                ).order_by().values('published_date').annotate(
                    count=models.Count('*'),
                ).values('count', date=models.F('published_date'))
            ),
        }
        if commit:
            self.save()

    def save(self, *args, **kwargs):
        if self.old_params != self.params:
            # Reset attributes
            transaction.on_commit(lambda: self.leads.clear())
            self.last_calculated_at = None
            self.stats = {}
            self.status = UnifiedConnectorSource.Status.NOT_PROCESSED
        super().save(*args, **kwargs)
        self.old_params = self.params


class UnifiedConnectorSourceLead(models.Model):
    """
    Link UnifiedConnectorSource with ConnectorLead
    """
    source = models.ForeignKey(UnifiedConnectorSource, on_delete=models.CASCADE)
    lead = models.ForeignKey(ConnectorLead, on_delete=models.CASCADE)
    blocked = models.BooleanField(default=False)
    already_added = models.BooleanField(default=False)
