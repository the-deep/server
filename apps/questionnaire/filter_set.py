from django.db import models
import django_filters

from .models import Questionnaire


class QuestionnaireFilterSet(django_filters.rest_framework.FilterSet):
    class Meta:
        model = Questionnaire
        fields = '__all__'
