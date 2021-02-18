from django.db import models
from django.contrib.postgres.fields import JSONField

from user.models import User
from project.models import Project
from entry.models import Entry


class Analysis(models.Model):
    title = models.CharField(max_length=255)
    team_lead = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    created_on = models.DateField(blank=True, null=True)
    analysis_pillars = models.ManyToManyField(
        'AnalysisPillar',
        blank=True,
    )

    def __str__(self):
        return self.title


class AnalysisPillar(models.Model):
    main_statement = models.TextField()
    information_gap = models.TextField()
    filters = JSONField(blank=True, null=True, default=None)
    assignee = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.main_statement


class AnalyticalStatement(models.Model):
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
        return self.statement


class AnalyticalStatementEntry(models.Model):
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
