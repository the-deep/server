from django.shortcuts import get_object_or_404
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin
from user_resource.serializers import UserResourceSerializer
from lead.models import Lead
from .models import (
    AssessmentTemplate,
    Assessment,
)


class AssessmentSerializer(RemoveNullFieldsMixin,
                           DynamicFieldsMixin, UserResourceSerializer):
    lead_title = serializers.CharField(source='lead.title',
                                       read_only=True)

    class Meta:
        model = Assessment
        fields = ('__all__')


class LeadAssessmentSerializer(RemoveNullFieldsMixin,
                               DynamicFieldsMixin, UserResourceSerializer):
    lead_title = serializers.CharField(source='lead.title',
                                       read_only=True)

    class Meta:
        model = Assessment
        fields = ('__all__')
        read_only_fields = ('lead',)

    def create(self, validated_data):
        # If this assessment is being created for the first time,
        # we want to set lead to the one which has its id in the url
        assessment = super(LeadAssessmentSerializer, self).create({
            **validated_data,
            'lead': get_object_or_404(Lead, pk=self.initial_data['lead']),
        })
        assessment.save()
        return assessment


class RecursiveSerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class ItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()


class TreeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    children = RecursiveSerializer(many=True, read_only=True)


class OptionSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField(source='title')


class FieldSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    tooltip = serializers.CharField()
    field_type = serializers.CharField(source='get_type')
    options = OptionSerializer(source='get_options',
                               many=True, read_only=True)


class GroupSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    fields = FieldSerializer(many=True, read_only=True)


class ScoreScaleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    color = serializers.CharField()
    value = serializers.IntegerField()
    default = serializers.BooleanField()


class ScoreQuestionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()


class ScorePillarSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    weight = serializers.FloatField()
    questions = ScoreQuestionSerializer(many=True, read_only=True)


class ScoreMatrixScaleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    value = serializers.IntegerField()
    default = serializers.BooleanField()


class ScoreMatrixRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()


class ScoreMatrixColumnSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()


class ScoreMatrixPillarSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    weight = serializers.FloatField()
    rows = ScoreMatrixRowSerializer(many=True, read_only=True)
    columns = ScoreMatrixColumnSerializer(many=True, read_only=True)
    scales = serializers.SerializerMethodField()

    def get_scales(self, pillar):
        data = {}
        for row in pillar.rows.all():
            row_data = {}
            for column in pillar.columns.all():
                scale = pillar.scales.filter(row=row, column=column).first()
                if not scale:
                    continue
                serializer = ScoreMatrixScaleSerializer(instance=scale)
                row_data[str(column.id)] = serializer.data
            data[str(row.id)] = row_data
        return data


class AssessmentTemplateSerializer(RemoveNullFieldsMixin,
                                   DynamicFieldsMixin, UserResourceSerializer):
    metadata_groups = GroupSerializer(source='metadatagroup_set',
                                      many=True, read_only=True)
    methodology_groups = GroupSerializer(source='methodologygroup_set',
                                         many=True, read_only=True)
    sectors = ItemSerializer(source='sector_set',
                             many=True, read_only=True)
    focuses = ItemSerializer(source='focus_set',
                             many=True, read_only=True)
    affected_groups = TreeSerializer(source='get_parent_affected_groups',
                                     many=True, read_only=True)

    priority_sectors = TreeSerializer(source='get_parent_priority_sectors',
                                      many=True, read_only=True)
    priority_issues = TreeSerializer(source='get_parent_priority_issues',
                                     many=True, read_only=True)
    specific_need_groups = ItemSerializer(source='specificneedgroup_set',
                                          many=True, read_only=True)
    affected_locations = ItemSerializer(source='affectedlocation_set',
                                        many=True, read_only=True)

    score_scales = ScoreScaleSerializer(source='scorescale_set',
                                        many=True, read_only=True)
    score_pillars = ScorePillarSerializer(source='scorepillar_set',
                                          many=True, read_only=True)
    score_matrix_pillars = ScoreMatrixPillarSerializer(
        source='scorematrixpillar_set',
        many=True,
        read_only=True,
    )

    score_buckets = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentTemplate
        fields = ('__all__')

    def get_score_buckets(self, template):
        buckets = template.scorebucket_set.all()
        return [
            [b.min_value, b.max_value, b.score]
            for b in buckets
        ]
