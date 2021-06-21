from django.db import models

from rest_framework.decorators import action
from rest_framework import (
    exceptions,
    permissions,
    views,
    response,
    viewsets,
    status
)

from deep.permissions import IsProjectMember
from entry.views import EntryFilterView

from lead.models import Lead
from .models import (
    Analysis,
    AnalysisPillar,
    AnalyticalStatement,
    DiscardedEntry
)
from .serializers import (
    AnalysisSerializer,
    AnalysisPillarSerializer,
    AnalyticalStatementSerializer,
    AnalysisSummarySerializer,
    DiscardedEntrySerializer,
)
from .filter_set import (
    AnalysisFilterSet,
    DiscardedEntryFilterSet,
)


class AnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    filterset_class = AnalysisFilterSet

    def get_queryset(self):
        return Analysis.objects.filter(project=self.kwargs['project_id']).select_related(
            'project',
            'team_lead',
        )

    @action(
        detail=False,
        url_path='summary'
    )
    def get_summary(self, request, project_id, filters=None, pk=None, version=None):
        from entry.filter_set import get_filtered_entries

        filters = filters or dict()
        entries_filter_data = filters.get('entries_filter_data', {})
        queryset = self.filter_queryset(self.get_queryset()).filter(project=project_id)
        queryset = queryset.prefetch_related(
            models.Prefetch(
                'analysispillar_set',
                queryset=AnalysisPillar.objects.defer(
                    'analysis'
                ).prefetch_related('analyticalstatement_set')
            )
        )
        total_entries = get_filtered_entries(self.request.user, entries_filter_data).count()
        total_sources = Lead.objects.filter(
            project=project_id
        ).annotate(entries_count=models.Count('entry')).filter(entries_count__gt=0).count()
        queryset = queryset.annotate(
            team_lead_name=models.F('team_lead__username'),
            dragged_entries=models.functions.Coalesce(
                models.Subquery(
                    AnalyticalStatement.objects.filter(
                        analysis_pillar__analysis=models.OuterRef('pk')
                    ).order_by().values('analysis_pillar__analysis').annotate(count=models.Count('entries', distinct=True))
                    .values('count')[:1],
                    output_field=models.IntegerField(),
                ), 0),
            sources_dragged=models.functions.Coalesce(
                models.Subquery(
                    AnalyticalStatement.objects.filter(
                        analysis_pillar__analysis=models.OuterRef('pk')
                    ).order_by().values('analysis_pillar__analysis').annotate(count=models.Count('entries__lead_id', distinct=True))
                    .values('count')[:1],
                    output_field=models.IntegerField(),
                ), 0),
            sources_discarded=models.functions.Coalesce(
                models.Subquery(
                    DiscardedEntry.objects.filter(
                        analysis_pillar__analysis=models.OuterRef('pk')
                    ).order_by().values('analysis_pillar__analysis').annotate(count=models.Count('entry__lead_id', distinct=True))
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
            analyzed_entries=models.F('dragged_entries') + models.F('discarded_entries'),
        )
        self.page = self.paginate_queryset(queryset)
        serializer = AnalysisSummarySerializer(
            self.page,
            many=True,
            partial=True,
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        url_path='pillar-overview'
    )
    def get_pillar_overview(self, request, project_id, pk=None, version=None):
        analysis = self.get_object()
        pillar_list = AnalysisPillar.objects.filter(
            analysis=analysis
        ).annotate(
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
            entries_analyzed=models.F('dragged_entries') + models.F('discarded_entries')
        )

        return response.Response(
            [
                {
                    'id': pillar.id,
                    'pillar_title': pillar.title,
                    'assignee': pillar.assignee.username,
                    'analytical_statements': AnalyticalStatement.objects.filter(
                        analysis_pillar=pillar
                    ).annotate(
                        entries_count=models.Count('entries', distinct=True)).values(
                        'entries_count', 'id', 'statement'
                    ),
                    'created_at': pillar.created_at,
                    'analytical_statement_count': AnalyticalStatement.objects.filter(analysis_pillar=pillar).count(),
                    'entries_analyzed': pillar.entries_analyzed
                } for pillar in pillar_list

            ]
        )

    @action(
        detail=True,
        url_path='clone-analysis',
        permission_classes=[IsProjectMember],
        methods=['post']
    )
    def clone_analysis(self, request, project_id, pk=None, version=None):
        analysis = self.get_object()
        cloned_title = request.data.get('title').strip()
        if not cloned_title:
            raise exceptions.ValidationError({
                'title': 'Title should be present',
            })
        new_analysis = analysis.clone_analysis()
        serializer = AnalysisSerializer(
            new_analysis,
            context={'request': request},
        )
        return response.Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class AnalysisPillarViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisPillarSerializer
    permissions_classes = [permissions.IsAuthenticated, IsProjectMember]

    def get_queryset(self):
        return AnalysisPillar.objects.filter(analysis=self.kwargs['analysis_id']).select_related(
            'analysis',
            'assignee'
        )


class AnalysisPillarDiscardedEntryViewSet(viewsets.ModelViewSet):
    serializer_class = DiscardedEntrySerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    filterset_class = DiscardedEntryFilterSet

    def get_queryset(self):
        return DiscardedEntry.objects.filter(analysis_pillar=self.kwargs['analysis_pillar_id'])

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            'analysis_pillar_id': self.kwargs.get('analysis_pillar_id'),
        }


class AnalysisPillarEntryViewSet(EntryFilterView):
    permission_classes = [IsProjectMember]

    def get_queryset(self):
        queryset = super().get_queryset()
        filters = self.get_entries_filters()
        analysis_pillar_id = self.kwargs['analysis_pillar_id']
        discarded_entries_qs = DiscardedEntry.objects.filter(analysis_pillar=analysis_pillar_id).values('entry')
        if filters.get('discarded'):
            return queryset.filter(id__in=discarded_entries_qs)
        return queryset.exclude(id__in=discarded_entries_qs)


class AnalyticalStatementViewSet(viewsets.ModelViewSet):
    serializer_class = AnalyticalStatementSerializer
    permissions_classes = [permissions.IsAuthenticated, IsProjectMember]

    def get_queryset(self):
        return AnalyticalStatement.objects.filter(analysis_pillar=self.kwargs['analysis_pillar_id']).select_related(
            'analysis_pillar',
        ).prefetch_related(
            'entries',
            'analyticalstatemententry_set',
        )


class DiscardedEntryOptionsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, version=None):
        options = [
                {
                    'key': tag.value,
                    'value': tag.name.title()
                } for tag in DiscardedEntry.TagType
        ]
        return response.Response(options)
