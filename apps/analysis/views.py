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
        ).prefetch_related('analysispillar_set')

    @action(
        detail=False,
        url_path='summary'
    )
    def get_summary(self, request, project_id, pk=None, version=None):
        queryset = self.filter_queryset(self.get_queryset()).filter(project=project_id)
        serializer = AnalysisSummarySerializer(queryset, many=True, partial=True)
        return response.Response(serializer.data)

    @action(
        detail=True,
        url_path='pillar-overview'
    )
    def get_pillar_overview(self, request, project_id, pk=None, version=None):
        analysis = self.get_object()
        pillar_list = AnalysisPillar.objects.filter(
            analysis=analysis
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
                    'analytical_statement_count': AnalyticalStatement.objects.filter(analysis_pillar=pillar).count()
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
        options = {
            'discarded_entries_tags': [
                {
                    'key': entry.value,
                    'value': entry.name.title()
                } for entry in DiscardedEntry.TagType
            ]
        }

        return response.Response(options)
