import copy

from django.db import models
from django_enumfield import enum
from django.db.models.functions import JSONObject
from django.db import connection as django_db_connection
from django.utils.translation import gettext_lazy as _

from project.mixins import ProjectEntityMixin
from user.models import User
from project.models import Project
from entry.models import Entry
from lead.models import Lead
from user_resource.models import UserResource


class Analysis(UserResource, ProjectEntityMixin):
    title = models.CharField(max_length=255)
    team_lead = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField()

    def __str__(self):
        return self.title

    def clone_analysis(self):
        analysis_cloned = copy.deepcopy(self)
        analysis_cloned.pk = None
        analysis_cloned.title = f'{self.title} (cloned)'
        analysis_cloned.save()
        return analysis_cloned

    @classmethod
    def get_analyzed_sources(cls, analysis_list):
        # NOTE: Used by AnalysisSummarySerializer, AnalysisViewSet.get_summary
        analysis_ids = [analysis.id for analysis in analysis_list]
        if len(analysis_ids) == 0:
            return {}

        leads_dragged = AnalyticalStatement.objects\
            .filter(analysis_pillar__analysis__in=analysis_ids)\
            .order_by().values('analysis_pillar__analysis', 'entries__lead_id')
        leads_discarded = DiscardedEntry.objects\
            .filter(analysis_pillar__analysis__in=analysis_ids)\
            .order_by().values('analysis_pillar__analysis', 'entry__lead_id')
        union_query = leads_dragged.union(leads_discarded).query

        # NOTE: Django ORM union isn't allowed inside annotation
        with django_db_connection.cursor() as cursor:
            raw_sql = f'''
                SELECT
                    u.analysis_id,
                    COUNT(DISTINCT(u.lead_id))
                FROM ({union_query}) as u
                GROUP BY u.analysis_id
            '''
            cursor.execute(raw_sql)
            return {
                analysis_id: lead_count
                for analysis_id, lead_count in cursor.fetchall()
            }

    @classmethod
    def annotate_for_analysis_summary(cls, project_id, queryset, user, filters=None):
        """
        This is used by AnalysisSummarySerializer and AnalysisViewSet.get_summary
        """
        # NOTE: Models aren't loaded yet, so lazy importing.
        from entry.filter_set import get_filtered_entries

        entries_filter_data = (filters or {}).get('entries_filter_data', {})
        total_entries = get_filtered_entries(user, entries_filter_data).count()
        total_sources = Lead.objects\
            .filter(project=project_id)\
            .annotate(entries_count=models.Count('entry'))\
            .filter(entries_count__gt=0)\
            .count()

        # Prefetch for AnalysisSummaryPillarSerializer.
        analysispillar_prefetch = models.Prefetch(
            'analysispillar_set',
            queryset=(
                AnalysisPillar.objects.select_related(
                    'assignee',
                    'assignee__profile',
                ).annotate(
                    dragged_entries=models.functions.Coalesce(models.Subquery(
                        AnalyticalStatement.objects.filter(
                            analysis_pillar=models.OuterRef('pk')
                        ).order_by().values('analysis_pillar').annotate(count=models.Count(
                            'entries',
                            distinct=True,
                            filter=models.Q(entries__lead_id__published_on__lte=models.OuterRef('analysis__end_date'))))
                        .values('count')[:1],
                        output_field=models.IntegerField(),
                    ), 0),
                    discarded_entries=models.functions.Coalesce(models.Subquery(
                        DiscardedEntry.objects.filter(
                            analysis_pillar=models.OuterRef('pk')
                        ).order_by().values('analysis_pillar').annotate(count=models.Count(
                            'entry',
                            distinct=True,
                            filter=models.Q(entry__lead_id__published_on__lte=models.OuterRef('analysis__end_date'))))
                        .values('count')[:1],
                        output_field=models.IntegerField(),
                    ), 0),
                    analyzed_entries=models.F('dragged_entries') + models.F('discarded_entries')
                )
            ),
        )

        # Subqueries
        dragged_entries_subquery = models.functions.Coalesce(
            models.Subquery(
                AnalyticalStatement.objects.filter(
                    analysis_pillar__analysis=models.OuterRef('pk')
                ).order_by().values('analysis_pillar__analysis')
                .annotate(count=models.Count(
                    'entries',
                    distinct=True,
                    filter=models.Q(entries__lead_id__published_on__lte=models.OuterRef('end_date'))))
                .values('count')[:1],
                output_field=models.IntegerField(),
            ), 0)
        discarded_entries_subquery = models.functions.Coalesce(
            models.Subquery(
                DiscardedEntry.objects.filter(
                    analysis_pillar__analysis=models.OuterRef('pk')
                ).order_by().values('analysis_pillar__analysis')
                .annotate(count=models.Count(
                    'entry',
                    distinct=True,
                    filter=models.Q(entry__lead_id__published_on__lte=models.OuterRef('end_date'))))
                .values('count')[:1],
                output_field=models.IntegerField(),
            ), 0)
        publication_date_subquery = models.Subquery(
            AnalyticalStatementEntry.objects.filter(
                analytical_statement__analysis_pillar__analysis=models.OuterRef('pk'),
            ).order_by().values('analytical_statement__analysis_pillar__analysis').annotate(
                published_on_min=models.Min('entry__lead__published_on'),
                published_on_max=models.Max('entry__lead__published_on'),
            ).annotate(
                publication_date=JSONObject(
                    start_date=models.F('published_on_min'),
                    end_date=models.F('published_on_max'),
                )
            ).values('publication_date')[:1],
            output_field=models.JSONField(),
        )

        return queryset.select_related(
            'team_lead',
            'team_lead__profile',
        ).prefetch_related(
            analysispillar_prefetch,
        ).annotate(
            team_lead_name=models.F('team_lead__username'),
            dragged_entries=dragged_entries_subquery,
            discarded_entries=discarded_entries_subquery,
            total_entries=models.Value(total_entries, output_field=models.IntegerField()),
            total_sources=models.Value(total_sources, output_field=models.IntegerField()),
            publication_date=publication_date_subquery,
            analyzed_entries=models.F('dragged_entries') + models.F('discarded_entries')
        )


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

    def can_get(self, user):
        return self.analysis.can_get(user)

    def can_modify(self, user):
        return self.analysis.can_modify(user)

    @classmethod
    def annotate_for_analysis_pillar_summary(cls, qs):
        analytical_statement_prefech = models.Prefetch(
            'analyticalstatement_set',
            queryset=(
                AnalyticalStatement.objects.annotate(
                    entries_count=models.Count('entries', distinct=True)
                )
            )
        )

        return qs\
            .prefetch_related(analytical_statement_prefech)\
            .annotate(
                dragged_entries=models.functions.Coalesce(
                    models.Subquery(
                        AnalyticalStatement.objects.filter(
                            analysis_pillar=models.OuterRef('pk')
                        ).order_by().values('analysis_pillar').annotate(count=models.Count(
                            'entries',
                            distinct=True,
                            filter=models.Q(entries__lead_id__published_on__lte=models.OuterRef('analysis__end_date'))))
                        .values('count')[:1],
                        output_field=models.IntegerField(),
                    ), 0),
                discarded_entries=models.functions.Coalesce(
                    models.Subquery(
                        DiscardedEntry.objects.filter(
                            analysis_pillar=models.OuterRef('pk')
                        ).order_by().values('analysis_pillar__analysis').annotate(count=models.Count(
                            'entry',
                            distinct=True,
                            filter=models.Q(entry__lead_id__published_on__lte=models.OuterRef('analysis__end_date'))))
                        .values('count')[:1],
                        output_field=models.IntegerField(),
                    ), 0),
                analyzed_entries=models.F('dragged_entries') + models.F('discarded_entries'),
            )


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

    def can_get(self, user):
        return self.analysis_pillar.can_get(user)

    def can_modify(self, user):
        return self.analysis_pillar.can_modify(user)

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

    def can_get(self, user):
        return self.analysis_pillar.can_get(user)

    def can_modify(self, user):
        return self.analysis_pillar.can_modify(user)

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

    def can_get(self, user):
        return self.analytical_statement.can_get(user)

    def can_modify(self, user):
        return self.analytical_statement.can_modify(user)

    class Meta:
        ordering = ('order',)
        unique_together = ('entry', 'analytical_statement')
