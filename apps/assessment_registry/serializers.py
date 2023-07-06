from rest_framework import serializers

from user_resource.serializers import UserResourceSerializer
from deep.serializers import ProjectPropertySerializerMixin, TempClientIdMixin

from .models import (
    AssessmentRegistry,
    MethodologyAttribute,
    AdditionalDocument,
    Summary,
    SummarySubSectorIssue,
    SummaryFocus,
    SummaryFocusSubSectorIssue,
    ScoreRating,
    ScoreAnalyticalDensity,
    Answer,
)


class MethodologyAttributeSerializer(TempClientIdMixin, serializers.ModelSerializer):
    class Meta:
        model = MethodologyAttribute
        fields = (
            "client_id", "data_collection_technique", "sampling_approach", "sampling_size",
            "proximity", "unit_of_analysis", "unit_of_reporting",
        )


class AdditionalDocumentSerializer(TempClientIdMixin, UserResourceSerializer):
    class Meta:
        model = AdditionalDocument
        fields = ("client_id", "document_type", "file", "external_link",)


class SummarySubSectorIssueSerializer(UserResourceSerializer, TempClientIdMixin):
    class Meta:
        model = SummarySubSectorIssue
        fields = ("summary_issue", "text", "order", "lead_preview_text_ref")


class SummarySerializer(UserResourceSerializer):

    class Meta:
        model = Summary
        fields = (
            "total_people_assessed", "total_dead", "total_injured", "total_missing",
            "total_people_facing_hum_access_cons", "percentage_of_people_facing_hum_access_cons",
        )


class SummaryFocusSerializer(UserResourceSerializer):
    class Meta:
        model = SummaryFocus
        fields = (
            "percentage_of_people_affected", "total_people_affected", "percentage_of_moderate",
            "percentage_of_severe", "percentage_of_critical", "percentage_in_need", "total_moderate",
            "total_severe", "total_critical", "total_in_need", "total_pop_assessed", "total_not_affected",
            "total_affected", "total_people_in_need", "total_people_moderately_in_need",
            "total_people_severly_in_need", "total_people_critically_in_need",
        )


class SummaryFocusIssueSerializer(UserResourceSerializer):
    class Meta:
        model = SummaryFocusSubSectorIssue
        fields = ("summary_issue", "focus", "text", "order", "lead_preview_text_ref",)


class ScoreRatingSerializer(UserResourceSerializer, TempClientIdMixin):
    class Meta:
        model = ScoreRating
        fields = ("client_id", "score_type", "rating", "reason",)


class ScoreAnalyticalDensitySerializer(UserResourceSerializer):
    class Meta:
        model = ScoreAnalyticalDensity
        fields = ("client_id", "sector", "value",)


class CNAAnswerSerializer(UserResourceSerializer):
    class Meta:
        model = Answer
        fields = ('question', 'answer')


class AssessmentRegistrySerializer(UserResourceSerializer, ProjectPropertySerializerMixin):
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
    summary_meta = SummarySerializer(source='summary', required=False, many=True)

    summary_subsector_issue = SummarySubSectorIssueSerializer(
        source="summary_sub_sector_issue_ary", many=True, required=False
    )
    summary_focus_meta = SummaryFocusSerializer(
        source='summary_focus', many=True, required=False
    )
    summary_focus_issue = SummaryFocusIssueSerializer(
        source="summary_focus_subsector_issue_ary", many=True, required=False
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
            "data_collection_start_date",
            "data_collection_end_date",
            "publication_date",
            "executive_summary",
            "lead_organizations",
            "international_partners",
            "donors",
            "national_partners",
            "governments",
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
            "language",
            "focuses",
            "sectors",
            "protection_info_mgmts",
            "affected_groups",
            "methodology_attributes",
            "additional_documents",
            "score_ratings",
            "matrix_score",
            "final_score",
            "score_analytical_density",
            "cna",
            "summary_meta",
            "summary_subsector_issue",
            "summary_focus_meta",
            "summary_focus_issue",
        )

    def validate(self, data):
        data['project'] = self.project
        error_dict = {}

        # validate for unique score types in score ratings
        unique_score_types = set()
        for d in data['score_ratings']:
            score_type = d.get("score_type")
            if score_type in unique_score_types:
                error_dict['score_ratings'] = "Score ratings should have unique score types"
            unique_score_types.add(score_type)

        # validate for unique sector in score analytical density
        unique_sector = set()
        for d in data['analytical_density']:
            sector = d.get("sector")
            if sector in unique_sector:
                error_dict['score_analytical_density'] = "Score analytical density should have unique sectors"
            unique_sector.add(sector)

        if error_dict:
            raise serializers.ValidationError(error_dict)
        return data
