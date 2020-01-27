from django.shortcuts import render
import django_filters
from rest_framework.decorators import action
from rest_framework import (
    viewsets,
    response,
)

from .models import (
    Questionnaire,
    QuestionBase,
    CrisisType,
)

from .serializers import (
    QuestionnaireSerializer,
    CrisisTypeSerializer,
)

from .filter_set import QuestionnaireFilterSet


class QuestionnaireViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionnaireSerializer

    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_class = QuestionnaireFilterSet

    def get_queryset(self):
        return Questionnaire.objects.all()

    @action(
        detail=False,
        url_path='options',
    )
    def get_options(self, request, version=None):
        options = {}
        options['enumerator_skill_options'] = [
            {
                'key': q[0],
                'value': q[1],
            } for q in
            QuestionBase.ENUMERATOR_SKILL_OPTIONS
        ]
        options['data_collection_technique_options'] = [
            {
                'key': q[0],
                'value': q[1],
            } for q in
            QuestionBase.DATA_COLLECTION_TECHNIQUE_OPTIONS
        ]
        options['question_importance_options'] = [
            {
                'key': q[0],
                'value': q[1],
            } for q in
            QuestionBase.IMPORTANCE_OPTIONS
        ]
        options['question_type_options'] = [
            {
                'key': q[0],
                'value': q[1],
            } for q in
            QuestionBase.TYPE_OPTIONS
        ]
        options['crisis_type_options'] = CrisisTypeSerializer(
            CrisisType.objects.all(),
            many=True,
        ).data

        return response.Response(options)


class CrisisTypeViewSet(viewsets.ModelViewSet):
    serializer_class = CrisisTypeSerializer

    def get_queryset(self):
        return CrisisType.objects.all()
