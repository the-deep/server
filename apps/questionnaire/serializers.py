import re
from django.shortcuts import get_object_or_404
from rest_framework.validators import UniqueTogetherValidator
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


class QuestionBaseSerializer(RemoveNullFieldsMixin, DynamicFieldsMixin, serializers.ModelSerializer):
    enumerator_skill_display = serializers.CharField(source='get_enumerator_skill_display', read_only=True)
    data_collection_technique_display = serializers.CharField(
        source='get_data_collection_technique_display', read_only=True)
    importance_display = serializers.CharField(source='get_importance_display', read_only=True)
    crisis_type_detail = CrisisTypeSerializer(source='crisis_type', read_only=True)

    @staticmethod
    def apply_order_action(question, action_meta, default_action=None):
        action = action_meta.get('action') or default_action
        value = action_meta.get('value')
        # NOTE: These methods (top, bottom, below and above) are provided by django-ordered-model
        if action in ['top', 'bottom']:
            getattr(question, action)()
        elif action in ['below', 'above']:
            if value is None:
                raise exceptions.ValidationError('Value is required for below|above actions')
            related_question = get_object_or_404(question._meta.model, pk=value)
            getattr(question, action)(related_question)

    def validate_name(self, value):
        if re.match("^[a-zA-Z_][A-Za-z0-9._-]*$", value) is None:
            raise exceptions.ValidationError(
                'Names have to start with a letter or an underscore'
                ' and can only contain letters, digits, hyphens, underscores, and periods'
            )
        return value

    def validate(self, data):
        data['questionnaire_id'] = int(self.context['questionnaire_id'])
        return data

    def create(self, data):
        question = super().create(data)
        # For handling order actions
        QuestionSerializer.apply_order_action(
            question,
            data.get('order_action') or {},
            'bottom',
        )
        return question


class QuestionSerializer(QuestionBaseSerializer):
    class Meta:
        model = Question
        fields = '__all__'
        read_only_fields = ('questionnaire',)
        validators = [
            UniqueTogetherValidator(
                queryset=Question.objects.all(),
                fields=['questionnaire', 'name'],
                message='Name should be unique',
            )
        ]


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
    data_collection_techniques_display = serializers.ListField(
        source='get_data_collection_techniques_display', read_only=True)
    crisis_types_detail = CrisisTypeSerializer(source='crisis_types', many=True, read_only=True)
    active_questions_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Questionnaire
        fields = '__all__'

    def create(self, validated_data):
        questionnaire = super().create(validated_data)
        return questionnaire


class QuestionnaireSerializer(MiniQuestionnaireSerializer):
    questions = QuestionSerializer(source='question_set', many=True, required=False)


class XFormSerializer(serializers.Serializer):
    file = serializers.FileField()


class KoboToolboxExportSerializer(serializers.Serializer):
    file = serializers.FileField()
    username = serializers.CharField()
    password = serializers.CharField()
