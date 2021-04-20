import copy

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError

from deep.settings import (
    ANALYTICAL_ENTRIES_COUNT,
    ANALYTICAL_STATEMENT_COUNT
)
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
    filters = JSONField(blank=True, null=True, default=None)
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

    def save(self, *args, **kwargs):
        if self.pk is None and \
            AnalyticalStatement.objects.filter(
                analysis_pillar=self.analysis_pillar).count() >= ANALYTICAL_STATEMENT_COUNT:
            raise ValidationError('Analytical statement count must be less than {}'.format(ANALYTICAL_STATEMENT_COUNT))
        return super().save(*args, **kwargs)


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

    def save(self, *args, **kwargs):
        if self.pk is None and \
            AnalyticalStatementEntry.objects.filter(
                analytical_statement=self.analytical_statement).count() >= ANALYTICAL_ENTRIES_COUNT:
            raise ValidationError('Analytical entries count must be less than {}'.format(ANALYTICAL_ENTRIES_COUNT))
        return super().save(*args, **kwargs)
