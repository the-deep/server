from .models import AssessmentRegistry, MethodologyAttribute, AdditionalDocument
from user_resource.serializers import UserResourceSerializer
from deep.serializers import ProjectPropertySerializerMixin
from rest_framework import serializers

class MethodologyAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MethodologyAttribute
        fields = (
            "id", "data_collection_technique", "sampling_approach", "sampling_size",
            "proximity", "unit_of_analysis", "unit_of_reporting",
        )


class AdditionalDocumentSerializer(UserResourceSerializer):
    class Meta:
        model = AdditionalDocument
        fields = ("id", "document_type", "file", "external_link",)


class AssessmentRegistrySerializer(UserResourceSerializer, ProjectPropertySerializerMixin):
    methodology_attributes = MethodologyAttributeSerializer(
        source='assessment_reg_methodology_attr', many=True, required=False
    )

    class Meta:
        model = AssessmentRegistry
        fields = (
            "id", "lead", "lead_group", "bg_countries", "bg_crisis_start_date",
            "cost_estimates_usd", "no_of_pages", "data_collection_start_date", "data_collection_end_date",
            "publication_date", "lead_organizations", "international_partners", "donors", "national_partners",
            "governments", "objectives", "data_collection_techniques", "sampling", "limitations", "locations",
            "bg_crisis_type", "bg_preparedness", "external_support", "coordinated_joint", "details_type",
            "family", "frequency", "confidentiality", "language", "focuses", "sectors", "protection_info_mgmts",
            "affected_groups", "methodology_attributes",
        )

    def validate(self, data):
        if not self.instance:
            data['project'] = self.context['request'].active_project
        return data
