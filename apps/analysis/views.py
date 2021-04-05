from django.shortcuts import render
from django.db import models
from django.utils import timezone

from rest_framework.decorators import action
from rest_framework import (
    exceptions,
    permissions,
    response,
    views,
    viewsets,
    serializers,
    status
)

from deep.permissions import IsProjectMember

from .models import (
    Analysis,
    AnalysisPillar,
    AnalyticalStatement,
    AnalyticalStatementEntry
)
from .serializers import (
    AnalysisSerializer,
    AnalysisPillarSerializer,
    AnalyticalStatementSerializer,
    AnalysisSummarySerializer,
)
from .filter_set import AnalysisFilterSet


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
                    'analytical_statement': AnalyticalStatement.objects.filter(
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

    @action(
        detail=True,
        url_path='statement',
        methods=['patch']
    )
    def update_statement(self, request, project_id, analysis_id, pk=None, version=None):
        instance = self.get_object()
        statements = request.data.get('analytical_statement', [])
        statement_maps = {x['id']: x for x in statements}
        statement_objs = AnalyticalStatement.objects.filter(
            analysis_pillar=instance,
            id__in=[x['id'] for x in statements]
        )

        for statement in statement_objs:
            serializer = AnalysisPillarSerializer(
                statement,
                data=statement_maps[statement.id],
                context={'request': request, 'view': self},
                partial=True,
            )
            serializer.is_valid()
            serializer.update(statement, statement_maps[statement.id])

        return response.Response(
            AnalysisPillarSerializer(instance, context={'request': request, 'view': self}).data,
        )


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
