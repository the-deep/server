from rest_framework import serializers, exceptions
from drf_dynamic_fields import DynamicFieldsMixin
from user_resource.serializers import UserResourceSerializer

from deep.serializers import (
    RemoveNullFieldsMixin,
)

from .models import (
    Questionnaire,
    Question,
    FrameworkQuestion,
    CrisisType,
)


class CrisisTypeSerializer(
    UserResourceSerializer,
    RemoveNullFieldsMixin,
):
    class Meta:
        fields = '__all__'
        model = CrisisType


class QuestionBaseSerializer(RemoveNullFieldsMixin, serializers.ModelSerializer):
    enumerator_skill_display = serializers.CharField(source='get_enumerator_skill_display', read_only=True)
    data_collection_technique_display = serializers.CharField(
        source='get_data_collection_technique_display', read_only=True)
    importance_display = serializers.CharField(source='get_importance_display', read_only=True)
    crisis_type_detail = CrisisTypeSerializer(source='crisis_type', read_only=True)


class QuestionSerializer(QuestionBaseSerializer):
    def validate(self, data):
        data['questionnaire_id'] = int(self.context['questionnaire_id'])
        return data

    class Meta:
        model = Question
        fields = '__all__'
        read_only_fields = ('questionnaire',)


class FrameworkQuestionSerializer(QuestionBaseSerializer):
    def validate(self, data):
        data['analysis_framework_id'] = int(self.context['af_id'])
        return data

    class Meta:
        model = FrameworkQuestion
        fields = ('__all__')
        read_only_fields = ('analysis_framework',)


class MiniQuestionnaireSerializer(
    RemoveNullFieldsMixin,
    DynamicFieldsMixin,
    UserResourceSerializer,
):
    enumerator_skill_display = serializers.CharField(source='get_enumerator_skill_display', read_only=True)
    data_collection_technique_display = serializers.CharField(
        source='get_data_collection_technique_display', read_only=True)

    crisis_type_detail = CrisisTypeSerializer(source='crisis_type', read_only=True)
    active_questions_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Questionnaire
        fields = '__all__'

    def create(self, validated_data):
        questionnaire = super().create(validated_data)
        return questionnaire


class QuestionnaireSerializer(MiniQuestionnaireSerializer):
    questions = QuestionSerializer(source='question_set', many=True, required=False)


class KoboToolboxExportSerializer(serializers.Serializer):
    file = serializers.FileField()
    access_code = serializers.CharField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False)

    def validate(self, data):
        if data.get('access_code') is None and (
                data.get('username') is None or data.get('password') is None
        ):
            raise exceptions.ValidationError('Requires access_code or [username, password]')
        return data
