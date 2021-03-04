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


class AnalysisCloneViewSet(views.APIView):
    permissions_classes = [permissions.IsAuthenticated]

    def post(self, request, analysis_id, version=None):
        if not Analysis.objects.filter(id=analysis_id).exists():
            raise exceptions.NotFound

        analysis = Analysis.objects.get(
            id=analysis_id
        )
        if not analysis.get_for(request.user):
            raise exceptions.PermissionDenied

        cloned_title = request.data.get('title')
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
            'entries__analytical_statement',)
