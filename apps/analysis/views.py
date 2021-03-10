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


class AnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]

    def get_queryset(self):
        return Analysis.objects.filter(project=self.kwargs['project_id']).select_related(
            'project',
            'team_lead',
        ).prefetch_related('analysispillar_set')

    @action(
        detail=True,
        url_path='summary'
    )
    def get_summary(self, request, project_id, pk=None, version=None):
        analysis = self.get_object()
        serializer = AnalysisSummarySerializer(analysis)
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
                    'created_on': pillar.created_on,
                    'analytical_statement_count': AnalyticalStatement.objects.filter(analysis_pillar=pillar).count()
                }for pillar in pillar_list

            ]
        )

    @action(
        detail=True,
        url_path='clone-analysis',
        methods=['post']
    )
    def clone_analysis(self, request, project_id, pk=None, version=None):
        analysis = self.get_object()
        if not analysis.get_for(request.user):
            raise exceptions.PermissionDenied

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
