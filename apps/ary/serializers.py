from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import (
    RemoveNullFieldsMixin,
    RecursiveSerializer,
)

from project.models import Project
from user_resource.serializers import UserResourceSerializer
from lead.serializers import (
    SimpleLeadSerializer,
    LegacySimpleLeadSerializer,
    ProjectEntitySerializer,
)
from lead.models import Lead, LeadGroup
from deep.models import Field
from geo.models import Region
from organization.models import Organization, OrganizationType
from organization.serializers import (
    ArySourceOrganizationSerializer,
    OrganizationTypeSerializer,
)

from .models import (
    AssessmentTemplate,
    Assessment,
    ScoreQuestionnaireSector,
    ScoreQuestionnaireSubSector,
    ScoreQuestionnaire,
)


class AssessmentSerializer(RemoveNullFieldsMixin,
                           DynamicFieldsMixin, ProjectEntitySerializer):
    lead_title = serializers.CharField(source='lead.title',
                                       read_only=True)
    lead_group_title = serializers.CharField(source='lead_group.title',
                                             read_only=True)
    project = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=Project.objects.all()
    )

    class Meta:
        model = Assessment
        fields = ('__all__')

    def create(self, data):
        if data.get('project') is None:
            if data.get('lead') is None:
                data['project'] = data['lead_group'].project
            else:
                data['project'] = data['lead'].project
        return super().create(data)


class LeadAssessmentSerializer(RemoveNullFieldsMixin,
                               DynamicFieldsMixin,
                               UserResourceSerializer):
    lead_title = serializers.CharField(source='lead.title',
                                       read_only=True)

    class Meta:
        model = Assessment
        fields = ('__all__')
        read_only_fields = ('lead', 'lead_group', 'project')

    def create(self, validated_data):
        # If this assessment is being created for the first time,
        # we want to set lead to the one which has its id in the url
        lead = get_object_or_404(Lead, pk=self.initial_data['lead'])
        assessment = super().create({
            **validated_data,
            'lead': lead,
            'project': lead.project,
        })
        assessment.save()
        return assessment


class LeadGroupAssessmentSerializer(RemoveNullFieldsMixin,
                                    DynamicFieldsMixin,
                                    UserResourceSerializer):
    lead_group_title = serializers.CharField(source='lead_group.title',
                                             read_only=True)
    leads = SimpleLeadSerializer(source='lead_group.lead_set',
                                 many=True,
                                 read_only=True)

    class Meta:
        model = Assessment
        fields = ('__all__')
        read_only_fields = ('lead', 'lead_group')

    def create(self, validated_data):
        # If this assessment is being created for the first time,
        # we want to set lead group to the one which has its id in the url
        assessment = super().create({
            **validated_data,
            'lead_group': get_object_or_404(
                LeadGroup,
                pk=self.initial_data['lead_group']
            ),
        })
        assessment.save()
        return assessment


class LegacyLeadGroupAssessmentSerializer(LeadGroupAssessmentSerializer):
    leads = LegacySimpleLeadSerializer(
        source='lead_group.lead_set', many=True, read_only=True,
    )


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
    is_required = serializers.BooleanField()
    title = serializers.CharField()
    tooltip = serializers.CharField()
    field_type = serializers.CharField()
    source_type = serializers.CharField()
    options = OptionSerializer(source='get_options',
                               many=True, read_only=True)

    class Meta:
        ref_name = 'AryFieldSerializer'


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


class ScoreQuestionnaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoreQuestionnaire
        fields = '__all__'


class ScoreQuestionnaireSubSectorSerializer(serializers.ModelSerializer):
    questions = ScoreQuestionnaireSerializer(
        source='scorequestionnaire_set', many=True, read_only=True,
    )

    class Meta:
        model = ScoreQuestionnaireSubSector
        fields = '__all__'


class ScoreQuestionnaireSectorSerializer(serializers.ModelSerializer):
    sub_sectors = ScoreQuestionnaireSubSectorSerializer(
        source='scorequestionnairesubsector_set', many=True, read_only=True,
    )

    class Meta:
        model = ScoreQuestionnaireSector
        fields = '__all__'


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
    underlying_factors = TreeSerializer(source='get_parent_underlying_factors',
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
    sources = serializers.SerializerMethodField()
    questionnaire_sector = ScoreQuestionnaireSectorSerializer(
        source='scorequestionnairesector_set', many=True, read_only=True,
    )

    class Meta:
        model = AssessmentTemplate
        fields = ('__all__')

    def get_score_buckets(self, template):
        buckets = template.scorebucket_set.all()
        return [
            [b.min_value, b.max_value, b.score]
            for b in buckets
        ]

    def get_sources(self, instance):
        def have_source(source_type):
            return AssessmentTemplate.objects.filter(
                Q(metadatagroup__fields__source_type=source_type) |
                Q(methodologygroup__fields__source_type=source_type),
                pk=instance.pk,
            ).exists()

        return {
            'countries': Region.objects.filter(public=True).extra(
                select={
                    'key': 'id',
                    'label': 'title',
                }
            ).values('key', 'label') if have_source(Field.COUNTRIES) else [],
            'organizations': ArySourceOrganizationSerializer(
                Organization.objects.all(),
                many=True,
                context=self.context,
            ).data
            if have_source(Field.ORGANIZATIONS or Field.DONORS) else [],
            'organization_type': OrganizationTypeSerializer(
                OrganizationType.objects.all(),
                many=True,
            ).data
            if have_source(Field.ORGANIZATIONS or Field.DONORS) else [],
        }
