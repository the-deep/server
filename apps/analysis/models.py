import copy
import json
from datetime import timedelta

from django.db import models
from django.db.models.functions import JSONObject
from django.db import connection as django_db_connection
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField

from utils.common import generate_sha256
from deep.number_generator import client_id_generator
from deep.filter_set import get_dummy_request
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
    # added to keep the track of cloned analysis
    cloned_from = models.ForeignKey(
        'Analysis',
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

    def __str__(self):
        return self.title

    def clone_analysis(self, title, end_date):
        analysis_cloned = copy.deepcopy(self)

        def _get_clone_pillar(obj, analysis_cloned_id):
            obj.cloned_from_id = obj.pk
            obj.pk = None
            obj.client_id = client_id_generator()
            obj.analysis_id = analysis_cloned_id
            return obj

        def _get_clone_pillar_statement(obj, analysis_pillar_id):
            obj.cloned_from_id = obj.pk
            obj.pk = None
            obj.client_id = client_id_generator()
            obj.analysis_pillar_id = analysis_pillar_id
            return obj

        def _get_clone_statement_entry(obj, analytical_statement_id):
            obj.pk = None
            obj.client_id = client_id_generator()
            obj.analytical_statement_id = analytical_statement_id
            return obj

        def _get_clone_discarded_entry(obj, analysis_pillar_id):
            obj.pk = None
            obj.analysis_pillar_id = analysis_pillar_id
            return obj

        analysis_cloned.pk = None
        analysis_cloned.client_id = client_id_generator()
        analysis_cloned.title = title
        analysis_cloned.end_date = end_date
        analysis_cloned.cloned_from = self
        analysis_cloned.save()
        # Clone pillars
        cloned_pillars = [
            _get_clone_pillar(analysis_pillar, analysis_cloned.pk)
            for analysis_pillar in self.analysispillar_set.all()
        ]
        cloned_pillar_id_map = {
            pillar.cloned_from_id: pillar.id
            for pillar in AnalysisPillar.objects.bulk_create(cloned_pillars)
        }

        # Clone discarded entries
        DiscardedEntry.objects.bulk_create(
            [
                _get_clone_discarded_entry(
                    discarded_entry,
                    cloned_pillar_id_map[discarded_entry.analysis_pillar_id],
                )
                for discarded_entry in DiscardedEntry.objects.filter(analysis_pillar__analysis=self)
            ]
        )

        # Clone statements
        cloned_statements = [
            _get_clone_pillar_statement(
                statement,
                cloned_pillar_id_map[statement.analysis_pillar_id],  # Use newly cloned pillar id
            )
            for statement in AnalyticalStatement.objects.filter(analysis_pillar__analysis=self)
        ]
        cloned_statement_id_map = {
            statement.cloned_from_id: statement.id
            for statement in AnalyticalStatement.objects.bulk_create(cloned_statements)
        }

        # Clone statement entries
        cloned_statement_entries = [
            _get_clone_statement_entry(
                statement_entry,
                cloned_statement_id_map[statement_entry.analytical_statement_id],  # Use newly cloned statement id
            )
            for statement_entry in AnalyticalStatementEntry.objects.filter(
                analytical_statement__analysis_pillar__analysis=self
            )
        ]
        AnalyticalStatementEntry.objects.bulk_create(cloned_statement_entries)

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
    def get_analyzed_entries(cls, analysis_list):
        # NOTE: Used by AnalysisSummarySerializer, AnalysisViewSet.get_summary
        analysis_ids = [analysis.id for analysis in analysis_list]
        if len(analysis_ids) == 0:
            return {}

        entries_dragged = AnalyticalStatementEntry.objects\
            .filter(
                analytical_statement__analysis_pillar__analysis__in=analysis_ids,
                entry__lead__published_on__lte=models.F('analytical_statement__analysis_pillar__analysis__end_date')
            )\
            .order_by().values('analytical_statement__analysis_pillar__analysis', 'entry')
        entries_discarded = DiscardedEntry.objects\
            .filter(
                analysis_pillar__analysis__in=analysis_ids,
                entry__lead__published_on__lte=models.F('analysis_pillar__analysis__end_date')
            )\
            .order_by().values('analysis_pillar__analysis', 'entry')
        union_query = entries_dragged.union(entries_discarded).query

        # NOTE: Django ORM union isn't allowed inside annotation
        with django_db_connection.cursor() as cursor:
            raw_sql = f'''
                SELECT
                    u.analysis_id,
                    COUNT(DISTINCT(u.entry_id))
                FROM ({union_query}) as u
                GROUP BY u.analysis_id
            '''
            cursor.execute(raw_sql)
            return {
                analysis_id: entry_count
                for analysis_id, entry_count in cursor.fetchall()
            }

    @classmethod
    def annotate_for_analysis_summary(cls, project_id, queryset, user):
        """
        This is used by AnalysisSummarySerializer and AnalysisViewSet.get_summary
        """
        # NOTE: Using the entries  and lead in the project for total entries and leads in analysis level
        total_sources = Lead.objects\
            .filter(project=project_id)\
            .annotate(entries_count=models.Count('entry'))\
            .filter(entries_count__gt=0)\
            .count()
        total_entries = Entry.objects.filter(project=project_id).count()

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
                            filter=models.Q(entries__lead__published_on__lte=models.OuterRef('analysis__end_date'))))
                        .values('count')[:1],
                        output_field=models.IntegerField(),
                    ), 0),
                    discarded_entries=models.functions.Coalesce(models.Subquery(
                        DiscardedEntry.objects.filter(
                            analysis_pillar=models.OuterRef('pk')
                        ).order_by().values('analysis_pillar').annotate(count=models.Count(
                            'entry',
                            distinct=True,
                            filter=models.Q(entry__lead__published_on__lte=models.OuterRef('analysis__end_date'))))
                        .values('count')[:1],
                        output_field=models.IntegerField(),
                    ), 0),
                    analyzed_entries=models.F('dragged_entries') + models.F('discarded_entries')
                )
            ),
        )

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
            total_entries=models.Value(total_entries, output_field=models.IntegerField()),
            total_sources=models.Value(total_sources, output_field=models.IntegerField()),
            publication_date=publication_date_subquery,
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
    # added to keep the track of cloned analysispillar
    cloned_from = models.ForeignKey(
        'AnalysisPillar',
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

    def __str__(self):
        return self.title

    def can_get(self, user):
        return self.analysis.can_get(user)

    def can_modify(self, user):
        return self.analysis.can_modify(user)

    def get_entries_qs(self, queryset=None, only_discarded=False):
        _queryset = queryset
        if _queryset is None:
            _queryset = Entry.objects.all()
        _queryset = _queryset.filter(
            project=self.analysis.project_id,
            lead__published_on__lte=self.analysis.end_date,
        )
        discarded_entries_qs = DiscardedEntry.objects.filter(analysis_pillar=self).values('entry')
        if only_discarded:
            return _queryset.filter(id__in=discarded_entries_qs)
        return _queryset.exclude(id__in=discarded_entries_qs)

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
                            filter=models.Q(entries__lead__published_on__lte=models.OuterRef('analysis__end_date'))))
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
                            filter=models.Q(entry__lead__published_on__lte=models.OuterRef('analysis__end_date'))))
                        .values('count')[:1],
                        output_field=models.IntegerField(),
                    ), 0),
                analyzed_entries=models.F('dragged_entries') + models.F('discarded_entries'),
            )


class DiscardedEntry(models.Model):
    """
    Discarded entries for AnalysisPillar
    """
    class TagType(models.IntegerChoices):
        REDUNDANT = 0, _('Redundant')
        TOO_OLD = 1, _('Too old')
        ANECDOTAL = 2, _('Anecdotal')
        OUTLIER = 3, _('Outlier')

    analysis_pillar = models.ForeignKey(
        AnalysisPillar,
        on_delete=models.CASCADE
    )
    entry = models.ForeignKey(
        Entry,
        on_delete=models.CASCADE
    )
    tag = models.IntegerField(choices=TagType.choices)

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
    # added to keep the track of cloned analysisstatement
    cloned_from = models.ForeignKey(
        'AnalyticalStatement',
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

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


# NLP Trigger Model -- Used as cache and tracking async data calculation
def entries_file_upload_to(instance, filename: str) -> str:
    return f'analysis/{type(instance).__name__.lower()}/entries/{filename}'


class TopicModel(UserResource, models.Model):
    class Status(models.IntegerChoices):
        PENDING = 0, 'Pending'
        STARTED = 1, 'Started'
        SUCCESS = 2, 'Success'
        FAILED = 3, 'Failed'
        SEND_FAILED = 4, 'Send Failed'

    entries_file = models.FileField(upload_to=entries_file_upload_to, max_length=255)
    status = models.PositiveSmallIntegerField(choices=Status.choices, default=Status.PENDING)

    analysis_pillar = models.ForeignKey(AnalysisPillar, on_delete=models.CASCADE)
    additional_filters = models.JSONField(default=dict)

    topicmodelcluster_set: models.QuerySet['TopicModelCluster']

    @staticmethod
    def _get_entries_qs(analysis_pillar, entry_filters):
        # Loading here to make sure models are loaded before filters
        from entry.filter_set import EntryGQFilterSet
        dummy_request = get_dummy_request(active_project=analysis_pillar.analysis.project_id)
        return EntryGQFilterSet(
            queryset=analysis_pillar.get_entries_qs(),  # Queryset from AnalysisPillar
            data=entry_filters,  # User Defined filter
            request=dummy_request,
        ).qs

    def get_entries_qs(self):
        return self._get_entries_qs(self.analysis_pillar, self.additional_filters)


class TopicModelCluster(models.Model):
    id: int
    topic_model = models.ForeignKey(TopicModel, on_delete=models.CASCADE)
    entries = models.ManyToManyField(Entry)


class EntriesCollectionNlpTriggerBase(UserResource, models.Model):
    class Status(models.IntegerChoices):
        PENDING = 0, 'Pending'
        STARTED = 1, 'Started'
        SUCCESS = 2, 'Success'
        FAILED = 3, 'Failed'
        SEND_FAILED = 4, 'Send Failed'

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    entries_id = ArrayField(models.IntegerField())
    entries_hash = models.CharField(max_length=256, db_index=True)   # Generated using entries_id
    entries_file = models.FileField(upload_to=entries_file_upload_to, max_length=255)
    status = models.PositiveSmallIntegerField(choices=Status.choices, default=Status.PENDING)

    CACHE_THRESHOLD_HOURS = 3

    class Meta:
        abstract = True

    @classmethod
    def get_existing(cls, entries_id):
        threshold = timezone.now() - timedelta(hours=cls.CACHE_THRESHOLD_HOURS)
        entries_hash = cls.get_entry_hash(entries_id)
        return cls.objects.filter(
            entries_hash=entries_hash,
            created_at__gte=threshold,
        ).exclude(
            status__in=[
                cls.Status.FAILED,
                cls.Status.SEND_FAILED,
            ],
        ).first()

    @staticmethod
    def get_valid_entries_id(project_id, entries_id):
        return list(
            Entry.objects.filter(
                project=project_id,
                id__in=entries_id,
            ).order_by('id').values_list('id', flat=True)
        )

    @staticmethod
    def get_entry_hash(entries_id):
        return generate_sha256(json.dumps(entries_id))

    def save(self, *args, **kwargs):
        self.entries_hash = self.get_entry_hash(self.entries_id)
        return super().save(*args, **kwargs)


class AutomaticSummary(EntriesCollectionNlpTriggerBase):
    summary = models.TextField()


class AnalyticalStatementNGram(EntriesCollectionNlpTriggerBase):
    # Structure: {keyword: count}
    unigrams = models.JSONField(default=dict)
    bigrams = models.JSONField(default=dict)
    trigrams = models.JSONField(default=dict)
