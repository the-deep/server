from rest_framework import serializers
from drf_dynamic_fields import DynamicFieldsMixin

from deep.serializers import (
    RemoveNullFieldsMixin,
    NestedCreateMixin,
    NestedUpdateMixin
)
from .models import (
    Analysis,
    AnalysisPillar,
)


class AnalysisPillarSerializer(serializers.ModelSerializer):

    class Meta:
        model = AnalysisPillar
        exclude = ('analysis',)


class AnalysisSerializer(RemoveNullFieldsMixin,
                         DynamicFieldsMixin,
                         NestedCreateMixin,
                         NestedUpdateMixin,):
    analysis_pillar = AnalysisPillarSerializer(many=True, source='analysispillar_set', required=False)

    class Meta:
        model = Analysis
        fields = '__all__'
