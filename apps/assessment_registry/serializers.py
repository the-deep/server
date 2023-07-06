from rest_framework import serializers

from user_resource.serializers import UserResourceSerializer
from deep.serializers import ProjectPropertySerializerMixin, TempClientIdMixin

from .models import (
    AssessmentRegistry,
    MethodologyAttribute,
    AdditionalDocument,
    ScoreRating,
    ScoreAnalyticalDensity,
)


class MethodologyAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MethodologyAttribute
        fields = (
            "client_id", "data_collection_technique", "sampling_approach", "sampling_size",
            "proximity", "unit_of_analysis", "unit_of_reporting",
        )


class AdditionalDocumentSerializer(UserResourceSerializer, TempClientIdMixin):
    class Meta:
        model = AdditionalDocument
        fields = ("client_id", "document_type", "file", "external_link",)


class ScoreRatingSerializer(UserResourceSerializer, TempClientIdMixin):
    class Meta:
        model = ScoreRating
        fields = ("client_id", "score_type", "rating", "reason",)


class ScoreAnalyticalDensitySerializer(UserResourceSerializer):
    class Meta:
        model = ScoreAnalyticalDensity
        fields = ("client_id", "sector", "value",)


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
