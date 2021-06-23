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
        pillar_cloned.pk = None
        pillar_cloned.client_id = None
        pillar_cloned.title = f'{title} (cloned)'
        pillar_cloned.save()
        [statement.clone_to(pillar_cloned) for statement
        in self.analyticalstatement_set.all()]
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

    def clone_to(self, analysis_pillar):
        cloned_statement = copy.deepcopy(self)
        cloned_statement.pk = None
        cloned_statement.client_id = None
        cloned_statement.statement = self.statement
        cloned_statement.analysis_pillar = analysis_pillar
        cloned_statement.save()
        [statement_entry.clone_to(cloned_statement) for statement_entry
        in self.analyticalstatemententry_set.all()]
        return cloned_statement

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

    def clone_to(self, analytical_statement):
        cloned_statement_entry = copy.deepcopy(self)
        cloned_statement_entry.pk = None
        cloned_statement_entry.client_id = None
        cloned_statement_entry.analytical_statement = analytical_statement
        cloned_statement_entry.save()
        return cloned_statement_entry
