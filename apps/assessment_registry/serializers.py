
from .models import AssessmentRegistry
from user_resource.serializers import UserResourceSerializer
from deep.serializers import RemoveNullFieldsMixin


class AssessmentRegistrySerializer(RemoveNullFieldsMixin, UserResourceSerializer):
    class Meta:
        model = AssessmentRegistry
        fields = (
            "id", "lead", "project", "lead_group", "bg_countries", "bg_crisis_start_date",
            "cost_estimates_usd", "no_of_pages", "data_collection_start_date", "data_collection_end_date",
            "publication_date", "lead_organizations", "international_partners", "donors", "national_partners",
            "governments", "objectives", "data_collection_techniques", "sampling", "limitations", "locations",
            "bg_crisis_type", "bg_preparedness", "external_support", "coordinated_joint", "details_type",
            "family", "frequency", "confidentiality", "language", "focuses", "sectors", "protection_info_mgmts",
            "affected_groups",
        )
