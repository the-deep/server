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
)

from .models import Analysis, AnalysisPillar
from .serializers import AnalysisSerializer


class AnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Analysis.objects.all()
