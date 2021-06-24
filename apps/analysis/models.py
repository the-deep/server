import copy

from django.db import models
from django.utils.translation import gettext_lazy as _
from django_enumfield import enum

from user.models import User
from project.models import Project
from entry.models import Entry
from lead.models import Lead
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

    @property
    def analyzed_sources(self):
        # FIXME: This generates N+1 query
        leads_dragged = AnalyticalStatement.objects.filter(
            analysis_pillar__analysis=self
        ).order_by().values('entries__lead_id').distinct()
        leads_discarded = DiscardedEntry.objects.filter(
           analysis_pillar__analysis=self
        ).order_by().values('entry__lead_id').distinct()
        leads_total = leads_dragged.union(leads_discarded)
        return leads_total.count()

    @classmethod
    def annotate_for_analysis_summary(cls, project_id, qs, user, filters=None):
        from entry.filter_set import get_filtered_entries

        filters = filters or dict()
        entries_filter_data = filters.get('entries_filter_data', {})
        total_entries = get_filtered_entries(user, entries_filter_data).count()
        total_sources = Lead.objects.filter(
            project=project_id
        ).annotate(entries_count=models.Count('entry')).filter(entries_count__gt=0).count()
        qs = qs.annotate(
            team_lead_name=models.F('team_lead__username'),
            dragged_entries=models.functions.Coalesce(
                models.Subquery(
                    AnalyticalStatement.objects.filter(
                        analysis_pillar__analysis=models.OuterRef('pk')
                    ).order_by().values('analysis_pillar__analysis').annotate(count=models.Count('entries', distinct=True))
                    .values('count')[:1],
                    output_field=models.IntegerField(),
                ), 0),
            discarded_entries=models.functions.Coalesce(
                models.Subquery(
                    DiscardedEntry.objects.filter(
                        analysis_pillar__analysis=models.OuterRef('pk')
                    ).order_by().values('analysis_pillar__analysis').annotate(count=models.Count('entry', distinct=True))
                    .values('count')[:1],
                    output_field=models.IntegerField(),
                ), 0),
            total_entries=models.Value(total_entries, output_field=models.IntegerField()),
            total_sources=models.Value(total_sources, output_field=models.IntegerField())
        ).annotate(
            analyzed_entries=models.F('dragged_entries') + models.F('discarded_entries')
        )
        return qs


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

    @classmethod
    def annotate_for_analysis_pillar_summary(cls, qs):
        qs = qs.annotate(
            dragged_entries=models.functions.Coalesce(
                models.Subquery(
                    AnalyticalStatement.objects.filter(
                        analysis_pillar=models.OuterRef('pk')
                    ).order_by().values('analysis_pillar').annotate(count=models.Count('entries', distinct=True))
                    .values('count')[:1],
                    output_field=models.IntegerField(),
                ), 0),
            discarded_entries=models.functions.Coalesce(
                models.Subquery(
                    DiscardedEntry.objects.filter(
                        analysis_pillar=models.OuterRef('pk')
                    ).order_by().values('analysis_pillar__analysis').annotate(count=models.Count('entry', distinct=True))
                    .values('count')[:1],
                    output_field=models.IntegerField(),
                ), 0),
        ).annotate(
            entries_analyzed=models.F('dragged_entries') + models.F('discarded_entries'),
            analytical_statement_count=models.functions.Coalesce(
                models.Subquery(
                    AnalyticalStatement.objects.filter(
                        analysis_pillar=models.OuterRef('pk')
                    ).order_by().values('analysis_pillar').annotate(count=models.Count('id', distinct=True))
                    .values('count')[:1],
                    output_field=models.IntegerField(),
                ),0)
        )
        return qs


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
