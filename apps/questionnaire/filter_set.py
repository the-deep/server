import django_filters

from .models import (
    Questionnaire,
    QuestionBase,
)


class QuestionnaireFilterSet(django_filters.rest_framework.FilterSet):
    data_collection_techniques = django_filters.MultipleChoiceFilter(
        choices=QuestionBase.DATA_COLLECTION_TECHNIQUE_OPTIONS,
        widget=django_filters.widgets.CSVWidget,
        method='filter_data_collection_techniques',
    )

    class Meta:
        model = Questionnaire
        fields = '__all__'

    def filter_data_collection_techniques(self, queryset, name, value):
        if len(value):
            return queryset.filter(data_collection_techniques__overlap=value)
        return queryset
