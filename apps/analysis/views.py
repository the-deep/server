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

from .models import Analysis, AnalysisPillar
from .serializers import (
    AnalysisSerializer,
    AnalysisMetaSerializer,
    AnalysisPillarSerializer,
)


class AnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return AnalysisMetaSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        return Analysis.objects.all()

    @action(
        detail=True,
        url_path='analysis-pillar',
        methods=['patch']
    )
    def update_pillar(self, request, pk=None, version=None):
        instance = self.get_object()
        pillars = request.data.get('analysis_pillar', [])
        pillar_maps = {x['id']: x for x in pillars}

        pillar_objs = AnalysisPillar.objects.filter(
            analysis=instance,
            id__in=[x['id'] for x in pillars]
        )
        for pillar in pillar_objs:
            serializer = AnalysisPillarSerializer(
                pillar,
                data=pillar_maps[pillar.id],
                context={'request': request},
                partial=True,
            )
            serializer.is_valid()
            serializer.update(pillar, pillar_maps[pillar.id])
        return response.Response(
            AnalysisMetaSerializer(instance, context={'request': request}).data,
        )


class AnalysisPillarViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisPillarSerializer
    permissions_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AnalysisPillar.objects.all()

    def create(self, request, version=None):
        return response.Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
