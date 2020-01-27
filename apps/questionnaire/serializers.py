from rest_framework import serializers
from drf_dynamic_fields import DynamicFieldsMixin
from user_resource.serializers import UserResourceSerializer

from deep.serializers import (
    RemoveNullFieldsMixin,
)

from analysis_framework.serializers import (
    AnalysisFrameworkSerializer
)

from project.models import (
    Project,
)

from .models import (
    QuestionBase,
    Questionnaire,
    Question,
    CrisisType,
)


class CrisisTypeSerializer(
    UserResourceSerializer,
    RemoveNullFieldsMixin,
):
    class Meta:
        fields = '__all__'
        model = CrisisType


class QuestionSerializer(
    RemoveNullFieldsMixin,
    UserResourceSerializer,
):
    enumerator_skill_detail = serializers.SerializerMethodField()
    data_collection_technique_detail = serializers.SerializerMethodField()
    importance_detail = serializers.SerializerMethodField()
    crisis_type_detail = CrisisTypeSerializer(source='crisis_type', read_only=True)

    class Meta:
        model = Question
        fields = '__all__'

    def get_enumerator_skill_detail(self, obj):
        enumerator_skill_map = dict(obj.ENUMERATOR_SKILL_OPTIONS)

        return {
            'key': obj.enumerator_skill,
            'value': enumerator_skill_map.get(obj.enumerator_skill)
        }

    def get_data_collection_technique_detail(self, obj):
        data_collection_technique_map = dict(obj.DATA_COLLECTION_TECHNIQUE_OPTIONS)

        return {
            'key': obj.data_collection_technique,
            'value': data_collection_technique_map.get(obj.data_collection_technique),
        }

    def get_importance_detail(self, obj):
        importance_map = dict(obj.IMPORTANCE_OPTIONS)

        return {
            'key': obj.importance,
            'value': importance_map.get(obj.importance)
        }


class QuestionnaireSerializer(
    RemoveNullFieldsMixin,
    DynamicFieldsMixin,
    UserResourceSerializer,
):
    enumerator_skill_detail = serializers.SerializerMethodField()
    data_collection_technique_detail = serializers.SerializerMethodField()

    project_framework_detail = AnalysisFrameworkSerializer(
        source='project.analysis_framework', read_only=True)

    questions = QuestionSerializer(source='question_set',
                                   many=True,
                                   required=False)
    crisis_type_detail = CrisisTypeSerializer(source='crisis_type', read_only=True)

    class Meta:
        model = Questionnaire
        fields = ('__all__')

    def create(self, validated_data):
        questionnaire = super().create(validated_data)
        return questionnaire

    def get_enumerator_skill_detail(self, obj):
        enumerator_skill_map = dict(QuestionBase.ENUMERATOR_SKILL_OPTIONS)

        return {
            'key': obj.enumerator_skill,
            'value': enumerator_skill_map.get(obj.enumerator_skill)
        }

    def get_data_collection_technique_detail(self, obj):
        data_collection_technique_map = dict(QuestionBase.DATA_COLLECTION_TECHNIQUE_OPTIONS)

        return {
            'key': obj.data_collection_technique,
            'value': data_collection_technique_map.get(obj.data_collection_technique),
        }
