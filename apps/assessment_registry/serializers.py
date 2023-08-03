from rest_framework import serializers

from user_resource.serializers import UserResourceSerializer
from deep.serializers import ProjectPropertySerializerMixin, TempClientIdMixin

from .models import (
    AssessmentRegistry,
    MethodologyAttribute,
    AdditionalDocument,
    SummaryIssue,
    Summary,
    SummarySubPillarIssue,
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


class IssueSerializer(UserResourceSerializer):
    class Meta:
        model = SummaryIssue
        fields = (
            'sub_pillar', 'sub_dimmension', 'parent', 'label'
        )

    def validate(self, data):
        if data.get('sub_pillar') is not None and data.get('sub_dimmension') is not None:
            raise serializers.ValidationError("Cannot select both sub_pillar and sub_dimmension field.")
        if data.get('parent') is not None:
            if data.get('sub_pillar') is not None:
                if data.get('sub_pillar') != data.get('parent').sub_pillar:
                    raise serializers.ValidationError("sub_pillar does not match between parent and child.")

            if data.get('sub_dimmension') is not None:
                if data.get('sub_dimmension') != data.get('parent').sub_dimmension:
                    raise serializers.ValidationError("sub_dimmension does not match between child and parent.")
        return data


class SummarySubPillarIssueSerializer(UserResourceSerializer, TempClientIdMixin):
    class Meta:
        model = SummarySubPillarIssue
        fields = ("summary_issue", "text", "order", "lead_preview_text_ref")


class SummaryMetaSerializer(UserResourceSerializer):
    class Meta:
        model = Summary
        fields = (
            "total_people_assessed", "total_dead", "total_injured", "total_missing",
            "total_people_facing_hum_access_cons", "percentage_of_people_facing_hum_access_cons",
        )


class SummaryFocusMetaSerializer(UserResourceSerializer):
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
        fields = ("client_id", "sector", "analysis_level_covered", "figure_provided",)


class CNAAnswerSerializer(TempClientIdMixin, UserResourceSerializer):
    class Meta:
        model = Answer
        fields = ('client_id', 'question', 'answer')


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
    summary_pillar_meta = SummaryMetaSerializer(source='summary', many=True, required=False)

    summary_sub_pillar_issue = SummarySubPillarIssueSerializer(
        source="summary_sub_sector_issue_ary", many=True, required=False
    )
    summary_dimmension_meta = SummaryFocusMetaSerializer(
        source='summary_focus', many=True, required=False
    )
    summary_sub_dimmension_issue = SummaryFocusIssueSerializer(
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
            "summary_pillar_meta",
            "summary_sub_pillar_issue",
            "summary_dimmension_meta",
            "summary_sub_dimmension_issue",
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

    def validate(self, data):
        data['project'] = self.project
        return data
