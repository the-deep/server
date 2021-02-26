from django.shortcuts import render
from django.db import models
from django.utils import timezone

from rest_framework.decorators import action
from rest_framework import (
    permissions,
    response,
    views,
    viewsets,
    serializers,
    status
)

from .models import (
    Analysis,
    AnalysisPillar,
    AnalyticalStatement,
    AnalyticalStatementEntry
)
from .serializers import (
    AnalysisSerializer,
    AnalysisMetaSerializer,
    AnalysisPillarSerializer,
    AnalyticalStatementSerializer,
    AnalysisSummarySerializer,
)


class AnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return AnalysisMetaSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        return Analysis.objects.filter(project=self.kwargs['project_id'])

    @action(
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        url_path='summary'
    )
    def get_summary(self, request, project_id, pk=None, version=None):
        analysis = self.get_object()
        serializer = AnalysisSummarySerializer(analysis)
        return response.Response(serializer.data)


class AnalysisPillarViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisPillarSerializer
    permissions_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AnalysisPillar.objects.filter(analysis=analysis_id)


class AnalyticalStatementViewSet(viewsets.ModelViewSet):
    serializer_class = AnalyticalStatementSerializer
    permissions_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AnalyticalStatement.objects.filter(analysis_pillar=self.kwargs['analysis_pillar_id'])
