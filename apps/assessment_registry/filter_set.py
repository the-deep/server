from deep.filter_set import generate_type_for_filter_set, OrderEnumMixin
from user_resource.filters import UserResourceGqlFilterSet
from .models import AssessmentRegistry
from utils.graphene.filters import IDListFilter, MultipleInputFilter
from .enums import (
    AssessmentRegistryAffectedGroupTypeEnum,
    AssessmentRegistryCoordinationTypeEnum,
    AssessmentRegistryDetailTypeEnum,
    AssessmentRegistryFamilyTypeEnum,
    AssessmentRegistryFrequencyTypeEnum,
    AssessmentRegistryFocusTypeEnum,
    AssessmentRegistrySectorTypeEnum,
)


class AssessmentDashboardFilterSet(OrderEnumMixin, UserResourceGqlFilterSet):
    stakeholder = IDListFilter(method="filter_stakeholder")
    lead_organization = IDListFilter(method="filter_lead_organization")
    location = IDListFilter(method="filter_location")
    affected_group = MultipleInputFilter(AssessmentRegistryAffectedGroupTypeEnum, method="filter_affected_group")
    family = MultipleInputFilter(AssessmentRegistryFamilyTypeEnum)
    frequency = MultipleInputFilter(AssessmentRegistryFrequencyTypeEnum)
    coordination_type = MultipleInputFilter(AssessmentRegistryCoordinationTypeEnum, field_name="coordinated_joint")
    assessment_type = MultipleInputFilter(AssessmentRegistryDetailTypeEnum, field_name="details_type")
    focuses = MultipleInputFilter(AssessmentRegistryFocusTypeEnum, method="filter_focuses")
    sectors = MultipleInputFilter(AssessmentRegistrySectorTypeEnum, method="filter_sectors")

    class Meta:
        model = AssessmentRegistry
        fields = ()

    def filter_stakeholder(self, qs, _, value):
        return qs if value is None else qs.filter(stakeholder__in=value)

    def filter_lead_organization(self, qs, _, value):
        return qs if value is None else qs.filter(stakeholder__in=value)

    def filter_location(self, qs, _, value):
        return (
            qs if value is None else qs.filter(locations__in=list(map(int, value)))
        )  # change value (list of decimal) into int list

    def filter_affected_group(self, qs, _, value):
        return qs if value is None else qs.filter(affected_groups__overlap=value)

    def filter_focuses(self, qs, _, value):
        return qs if value is None else qs.filter(focuses__overlap=value)

    def filter_sectors(self, qs, _, value):
        return qs if value is None else qs.filter(sectors__overlap=value)


AssessmentDashboardFilterDataType, AssessmentDashboardFilterDataInputType = generate_type_for_filter_set(
    AssessmentDashboardFilterSet,
    "project.schema.ProjectListType",
    "AssessmentDashboardFilterDataType",
    "AssessmentDashboardFilterDataInputType",
)
