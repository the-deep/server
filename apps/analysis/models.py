import copy

from django.db import models
from django.utils.translation import gettext_lazy as _
from django_enumfield import enum

from user.models import User
from project.models import Project
from entry.models import Entry
from user_resource.models import UserResource


class Analysis(UserResource):
    title = models.CharField(max_length=255)
    team_lead = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.title

    def clone_analysis(self):
        analysis_cloned = copy.deepcopy(self)
        analysis_cloned.pk = None
        analysis_cloned.title = f'{self.title} (cloned)'
        analysis_cloned.save()
        return analysis_cloned


class AnalysisPillar(UserResource):
    title = models.CharField(max_length=255)
    main_statement = models.TextField(blank=True)
    information_gap = models.TextField(blank=True)
    filters = models.JSONField(blank=True, null=True, default=None)
    assignee = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.title

    def clone_pillar(self, title):
        pillar_cloned = copy.deepcopy(self)

        def _get_clone_ready(obj, pillar_cloned):
            obj.client_id = None
            obj.pk = None
            obj.analysis_pillar = pillar_cloned
            return obj

        pillar_cloned.pk = None
        pillar_cloned.client_id = None
        pillar_cloned.title = title
        pillar_cloned.save()
        analytical_statements = self.analyticalstatement_set.all()
        AnalyticalStatement.objects.bulk_create([
            _get_clone_ready(analytical_statement, pillar_cloned) for analytical_statement in analytical_statements
        ])
        return pillar_cloned


class DiscardedEntry(models.Model):
    """
    Discarded entries for AnalysisPillar
    """
    class TagType(enum.Enum):
        REDUNDANT = 0
        TOO_OLD = 1
        ANECDOTAL = 2
        OUTLIER = 3

        __labels__ = {
            REDUNDANT: _('Redundant'),
            TOO_OLD: _('Too old'),
            ANECDOTAL: _('Anecdotal'),
            OUTLIER: _('Outlier'),
        }

    analysis_pillar = models.ForeignKey(
        AnalysisPillar,
        on_delete=models.CASCADE
    )
    entry = models.ForeignKey(
        Entry,
        on_delete=models.CASCADE
    )
    tag = enum.EnumField(TagType)

    class Meta:
        unique_together = ('entry', 'analysis_pillar')

    def __str__(self):
        return f'{self.analysis_pillar} - {self.entry}'


class AnalyticalStatement(UserResource):
    statement = models.TextField()
    entries = models.ManyToManyField(
        Entry,
        through='AnalyticalStatementEntry',
        through_fields=('analytical_statement', 'entry'),
        blank=True,
    )
    analysis_pillar = models.ForeignKey(
        AnalysisPillar,
        on_delete=models.CASCADE
    )
    include_in_report = models.BooleanField(default=False)
    order = models.IntegerField()

    class Meta:
        ordering = ('order',)

    def __str__(self):
        return self.statement and self.statement[:255]


class AnalyticalStatementEntry(UserResource):
    entry = models.ForeignKey(
        Entry,
        on_delete=models.CASCADE
    )
    analytical_statement = models.ForeignKey(
        AnalyticalStatement,
        on_delete=models.CASCADE
    )
    order = models.IntegerField()

    class Meta:
        ordering = ('order',)
        unique_together = ('entry', 'analytical_statement')
