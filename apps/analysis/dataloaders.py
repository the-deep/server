from promise import Promise
from collections import defaultdict

from django.utils.functional import cached_property
from django.db import models

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from .models import (
    Analysis,
    AnalysisPillar,
    AnalyticalStatement,
    AnalyticalStatementEntry,
    DiscardedEntry,
)


class AnalysisPublicationDatesLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AnalyticalStatementEntry.objects.filter(
            analytical_statement__analysis_pillar__analysis__in=keys,
        ).order_by().values('analytical_statement__analysis_pillar__analysis').annotate(
            published_on_min=models.Min('entry__lead__published_on'),
            published_on_max=models.Max('entry__lead__published_on'),
        ).values_list(
            'published_on_min',
            'published_on_max',
            'analytical_statement__analysis_pillar__analysis'
        )
        _map = {}
        for start_date, end_date, _id in qs:
            _map[_id] = dict(
                # For AnalysisPublicationDatesType
                start_date=start_date,
                end_date=end_date,
            )
        return Promise.resolve([_map.get(key) for key in keys])


class AnalysisAnalyzedEntriesLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        _map = Analysis.get_analyzed_entries([
            Analysis(id=key) for key in keys
        ])
        return Promise.resolve([_map.get(key, 0) for key in keys])


class AnalysisAnalyzedLeadsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        _map = Analysis.get_analyzed_sources([
            Analysis(id=key) for key in keys
        ])
        return Promise.resolve([_map.get(key, 0) for key in keys])


class AnalysisAnalysisPillarsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AnalysisPillar.objects.filter(analysis__in=keys)
        _map = defaultdict(list)
        for analysis_pillar in qs:
            _map[analysis_pillar.analysis_id].append(analysis_pillar)
        return Promise.resolve([_map[key] for key in keys])


class AnalysisPillarAnalyticalStatementsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AnalyticalStatement.objects.filter(analysis_pillar__in=keys)
        _map = defaultdict(list)
        for statement in qs:
            _map[statement.analysis_pillar_id].append(statement)
        return Promise.resolve([_map[key] for key in keys])


class AnalyticalStatementEntriesLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AnalyticalStatementEntry.objects.filter(analytical_statement__in=keys)
        _map = defaultdict(list)
        for statement_entry in qs:
            _map[statement_entry.analytical_statement_id].append(statement_entry)
        return Promise.resolve([_map[key] for key in keys])


class AnalysisPillarsAnalyzedEntriesLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AnalysisPillar.objects\
            .filter(id__in=keys)\
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
            ).values_list('id', 'analyzed_entries')
        _map = {
            _id: count
            for _id, count in qs
        }
        return Promise.resolve([_map.get(key, 0) for key in keys])


class AnalysisStatementAnalyzedEntriesLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AnalyticalStatement.objects.filter(id__in=keys).annotate(
            count=models.Count('entries', distinct=True)
        ).values('id', 'count')
        _map = {
            _id: count
            for _id, count in qs
        }
        return Promise.resolve([_map.get(key, 0) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def analysis_publication_date(self):
        return AnalysisPublicationDatesLoader(context=self.context)

    @cached_property
    def analysis_analyzed_entries(self):
        return AnalysisAnalyzedEntriesLoader(context=self.context)

    @cached_property
    def analysis_analyzed_leads(self):
        return AnalysisAnalyzedLeadsLoader(context=self.context)

    @cached_property
    def analysis_analysis_pillars(self):
        return AnalysisAnalysisPillarsLoader(context=self.context)

    @cached_property
    def analysis_pillars_analyzed_entries(self):
        return AnalysisPillarsAnalyzedEntriesLoader(context=self.context)

    @cached_property
    def analysis_statement_analyzed_entries(self):
        return AnalysisStatementAnalyzedEntriesLoader(context=self.context)

    @cached_property
    def analysis_pillar_analytical_statements(self):
        return AnalysisPillarAnalyticalStatementsLoader(context=self.context)

    @cached_property
    def analytical_statement_entries(self):
        return AnalyticalStatementEntriesLoader(context=self.context)
