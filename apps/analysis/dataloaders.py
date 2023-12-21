from promise import Promise
from collections import defaultdict

from django.utils.functional import cached_property
from django.db import models

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from .models import (
    Analysis,
    AnalysisPillar,
    AnalysisReport,
    AnalyticalStatement,
    AnalyticalStatementEntry,
    DiscardedEntry,
    TopicModelCluster,
    AnalysisReportUpload,
    AnalysisReportContainerData,
    AnalysisReportContainer,
    AnalysisReportSnapshot,
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


class AnalysisTopicModelClusterEntryLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = TopicModelCluster.entries.through.objects.filter(
            topicmodelcluster__in=keys,
        ).select_related('entry').order_by('topicmodelcluster', 'entry_id')
        _map = defaultdict(list)
        for cluster_entry in qs:
            _map[cluster_entry.topicmodelcluster_id].append(cluster_entry.entry)
        return Promise.resolve([_map.get(key, []) for key in keys])


# -------------- Report Module -------------------------------
class AnalysisReportUploadsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AnalysisReportUpload.objects.filter(
            id__in=keys,
        )
        _map = {
            item.pk: item
            for item in qs
        }
        return Promise.resolve([_map.get(key, []) for key in keys])


class AnalysisReportContainerDataByContainerLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AnalysisReportContainerData.objects.filter(
            container__in=keys,
        )
        _map = defaultdict(list)
        for item in qs:
            _map[item.container_id].append(item)
        return Promise.resolve([_map.get(key, []) for key in keys])


class OrganizationByAnalysisReportLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AnalysisReport.organizations.through.objects.filter(
            analysisreport__in=keys,
        ).select_related('organization')
        _map = defaultdict(list)
        for item in qs:
            _map[item.analysisreport_id].append(item.organization)
        return Promise.resolve([_map[key] for key in keys])


class ReportUploadByAnalysisReportLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AnalysisReportUpload.objects.filter(
            report__in=keys,
        )
        _map = defaultdict(list)
        for item in qs:
            _map[item.report_id].append(item)
        return Promise.resolve([_map[key] for key in keys])


class AnalysisReportContainerByAnalysisReportLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AnalysisReportContainer.objects.filter(
            report__in=keys,
        )
        _map = defaultdict(list)
        for item in qs:
            _map[item.report_id].append(item)
        return Promise.resolve([_map[key] for key in keys])


class LatestReportSnapshotByAnalysisReportLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = AnalysisReportSnapshot.objects.filter(
            report__in=keys,
        ).order_by('report_id', '-published_on').distinct('report_id')
        _map = {
            snapshot.report_id: snapshot
            for snapshot in qs
        }
        return Promise.resolve([_map.get(key) for key in keys])


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
    def analytical_statement_analyzed_entries(self):
        return AnalysisStatementAnalyzedEntriesLoader(context=self.context)

    @cached_property
    def analysis_pillar_analytical_statements(self):
        return AnalysisPillarAnalyticalStatementsLoader(context=self.context)

    @cached_property
    def analytical_statement_entries(self):
        return AnalyticalStatementEntriesLoader(context=self.context)

    @cached_property
    def topic_model_cluster_entries(self):
        return AnalysisTopicModelClusterEntryLoader(context=self.context)

    @cached_property
    def analysis_report_uploads(self):
        return AnalysisReportUploadsLoader(context=self.context)

    @cached_property
    def analysis_report_container_data_by_container(self):
        return AnalysisReportContainerDataByContainerLoader(context=self.context)

    @cached_property
    def organization_by_analysis_report(self):
        return OrganizationByAnalysisReportLoader(context=self.context)

    @cached_property
    def analysis_report_uploads_by_analysis_report(self):
        return ReportUploadByAnalysisReportLoader(context=self.context)

    @cached_property
    def analysis_report_container_by_analysis_report(self):
        return AnalysisReportContainerByAnalysisReportLoader(context=self.context)

    @cached_property
    def latest_report_snapshot_by_analysis_report(self):
        return LatestReportSnapshotByAnalysisReportLoader(context=self.context)
