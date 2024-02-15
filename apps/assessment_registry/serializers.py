from rest_framework import serializers

from .utils import get_hierarchy_level
from user_resource.serializers import UserResourceSerializer
from deep.serializers import (
    ProjectPropertySerializerMixin,
    TempClientIdMixin,
    IntegerIDField,
)
from .models import (
    AssessmentRegistry,
    MethodologyAttribute,
    AdditionalDocument,
    SummaryIssue,
    Summary,
    SummarySubPillarIssue,
    SummaryFocus,
    SummarySubDimensionIssue,
    ScoreRating,
    ScoreAnalyticalDensity,
    Answer,
    AssessmentRegistryOrganization,
)


class AssessmentRegistryOrganizationSerializer(
    TempClientIdMixin,
    UserResourceSerializer,
    serializers.ModelSerializer
):
    id = IntegerIDField(required=False)

    class Meta:
        model = AssessmentRegistryOrganization
        fields = ('id', 'client_id', 'organization', 'organization_type')


class MethodologyAttributeSerializer(TempClientIdMixin, serializers.ModelSerializer):
    id = IntegerIDField(required=False)

    class Meta:
        model = MethodologyAttribute
        fields = (
            "id", "client_id", "data_collection_technique", "sampling_approach", "sampling_size",
            "proximity", "unit_of_analysis", "unit_of_reporting",
        )


class AdditionalDocumentSerializer(TempClientIdMixin, UserResourceSerializer):
    id = IntegerIDField(required=False)

    class Meta:
        model = AdditionalDocument
        fields = ("id", "client_id", "document_type", "file", "external_link",)


class IssueSerializer(UserResourceSerializer):
    class Meta:
        model = SummaryIssue
        fields = (
            'sub_pillar', 'sub_dimension', 'parent', 'label'
        )

    def validate(self, data):
        sub_pillar = data.get('sub_pillar')
        sub_dimension = data.get('sub_dimension')
        parent = data.get('parent')

        if all([sub_pillar, sub_dimension]):
            raise serializers.ValidationError("Cannot select both sub_pillar and sub_dimension field.")
        if not any([sub_pillar, sub_dimension]):
            raise serializers.ValidationError("Either sub_pillar or sub_dimension must be selected")

        if parent:
            if sub_pillar and sub_pillar != parent.sub_pillar:
                raise serializers.ValidationError("sub_pillar does not match between parent and child.")
            if sub_dimension and sub_dimension != parent.sub_dimension:
                raise serializers.ValidationError("sub_dimension does not match between child and parent.")

            hierarchy_level = get_hierarchy_level(parent)
            if hierarchy_level > 2:
                raise serializers.ValidationError("Cannot create issue more than two level of hierarchy")
        return data


class SummarySubPillarIssueSerializer(UserResourceSerializer, TempClientIdMixin):
    id = IntegerIDField(required=False)

    class Meta:
        model = SummarySubPillarIssue
        fields = ("id", "client_id", "summary_issue", "text", "order", "lead_preview_text_ref")


class SummaryMetaSerializer(UserResourceSerializer):
    id = IntegerIDField(required=False)

    class Meta:
        model = Summary
        fields = (
            "id", "total_people_assessed", "total_dead", "total_injured", "total_missing",
            "total_people_facing_hum_access_cons", "percentage_of_people_facing_hum_access_cons",
        )


class SummaryFocusMetaSerializer(UserResourceSerializer, TempClientIdMixin):
    id = IntegerIDField(required=False)

    class Meta:
        model = SummaryFocus
        fields = (
            "id", "client_id", "sector", "percentage_of_people_affected", "total_people_affected", "percentage_of_moderate",
            "percentage_of_severe", "percentage_of_critical", "percentage_in_need", "total_moderate",
            "total_severe", "total_critical", "total_in_need",
        )


class SummarySubDimensionSerializer(UserResourceSerializer, TempClientIdMixin):
    id = IntegerIDField(required=False)

    class Meta:
        model = SummarySubDimensionIssue
        fields = (
            "id",
            "client_id",
            "summary_issue",
            "sector",
            "text",
            "order",
            "lead_preview_text_ref",
        )


class ScoreRatingSerializer(UserResourceSerializer, TempClientIdMixin):
    id = IntegerIDField(required=False)

    class Meta:
        model = ScoreRating
        fields = ("id", "client_id", "score_type", "rating", "reason",)


class ScoreAnalyticalDensitySerializer(UserResourceSerializer, TempClientIdMixin):
    id = IntegerIDField(required=False)

    class Meta:
        model = ScoreAnalyticalDensity
        fields = ("id", "client_id", "sector", "analysis_level_covered", "figure_provided", "score",)


class CNAAnswerSerializer(TempClientIdMixin, UserResourceSerializer):
    id = IntegerIDField(required=False)

    class Meta:
        model = Answer
        fields = ("id", 'client_id', 'question', 'answer')


class AssessmentRegistrySerializer(UserResourceSerializer, ProjectPropertySerializerMixin):
    stakeholders = AssessmentRegistryOrganizationSerializer(
        source='assessmentregistryorganization_set',
        many=True,
        required=False,
    )
    methodology_attributes = MethodologyAttributeSerializer(
        many=True, required=False
    )
    additional_documents = AdditionalDocumentSerializer(
        many=True, required=False
    )
    score_ratings = ScoreRatingSerializer(
        many=True, required=False
    )
    score_analytical_density = ScoreAnalyticalDensitySerializer(
        source="analytical_density", many=True, required=False
    )
    cna = CNAAnswerSerializer(
        source='answer',
        many=True,
        required=False
    )
    summary_pillar_meta = SummaryMetaSerializer(source='summary', required=False)

    summary_sub_pillar_issue = SummarySubPillarIssueSerializer(
        source="summary_sub_sector_issue_ary", many=True, required=False
    )
    summary_dimension_meta = SummaryFocusMetaSerializer(
        source='summary_focus', many=True, required=False
    )
    summary_sub_dimension_issue = SummarySubDimensionSerializer(
        source="summary_focus_subsector_issue_ary", many=True, required=False
    )
    additional_documents = AdditionalDocumentSerializer(
        many=True, required=False
    )

    class Meta:
        model = AssessmentRegistry
        fields = (
            "id",
            "lead",
            "bg_countries",
            "bg_crisis_start_date",
            "cost_estimates_usd",
            "no_of_pages",
            "status",
            "data_collection_start_date",
            "data_collection_end_date",
            "publication_date",
            "executive_summary",
            "objectives",
            "data_collection_techniques",
            "sampling",
            "limitations",
            "locations",
            "bg_crisis_type",
            "bg_preparedness",
            "external_support",
            "coordinated_joint",
            "details_type",
            "family",
            "frequency",
            "confidentiality",
            "stakeholders",
            "language",
            "focuses",
            "sectors",
            "protection_info_mgmts",
            "affected_groups",
            "methodology_attributes",
            "additional_documents",
            "score_ratings",
            "score_analytical_density",
            "cna",
            "summary_pillar_meta",
            "summary_sub_pillar_issue",
            "summary_dimension_meta",
            "summary_sub_dimension_issue",
            "metadata_complete",
            "additional_document_complete",
            "focus_complete",
            "methodology_complete",
            "summary_complete",
            "cna_complete",
            "score_complete"
        )

    def validate_score_ratings(self, data):
        unique_score_types = set()
        for d in data:
            score_type = d.get("score_type")
            if score_type in unique_score_types:
                raise serializers.ValidationError("Score ratings should have unique score types")
            unique_score_types.add(score_type)
        return data

    def validate_score_analytical_density(self, data):
        unique_sector = set()
        for d in data:
            sector = d.get("sector")
            if sector in unique_sector:
                raise serializers.ValidationError("Score analytical density should have unique sectors")
            unique_sector.add(sector)
        return data

    def validate_stakeholders(self, data):
        stakeholders_list = []
        for org in data:
            org.pop('client_id', None)
            if org in stakeholders_list:
                raise serializers.ValidationError('Dublicate organization selected')
            stakeholders_list.append(org)

    def validate_cna(self, data):
        question_list = []
        for question in data:
            question.pop('client_id', None)
            if question in question_list:
                raise serializers.ValidationError('Dublicate question selected')
            question_list.append(question)

    def validate(self, data):
        data['project'] = self.project
        return data
