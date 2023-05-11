import graphene
from user_resource.schema import UserResourceMixin
from graphene_django import DjangoObjectType
from utils.graphene.enums import EnumDescription
from .models import AssessmentRegistry, MethodologyAttribute, AdditionalDocument
from .enums import (
    CrisisTypeEnum,
    PreparednessTypeEnum,
    ExternalSupportTypeEnum,
    CoordinationTypeEnum,
    DetailTypeEnum,
    FamilyTypeEnum,
    FrequencyTypeEnum,
    ConfidentialityTypeEnum,
    LanguageTypeEnum,
    FocusTypeEnum,
    SectorTypeEnum,
    ProtectionInfoTypeEnum,
    AffectedGroupTypeEnum,
    DataCollectionTechniqueTypeEnum,
    SamplingApproachTypeEnum,
    ProximityTypeEnum,
    UnitOfAnalysisTypeEnum,
    UnitOfReportingTypeEnum,
    DocumentTypeEnum,
)


class MethodologyAttributeType(DjangoObjectType, UserResourceMixin):
    class Meta:
        model = MethodologyAttribute
        fields = ("id", "proximity",)

    data_collection_technique = graphene.Field(DataCollectionTechniqueTypeEnum, required=True)
    data_collection_technique_display = EnumDescription(source='get_affected_groups_display', required=True)
    sampling_approach = graphene.Field(SamplingApproachTypeEnum, required=True)
    sampling_appraoch_display = EnumDescription(source='get_affected_groups_display', required=True)
    proximity = graphene.Field(ProximityTypeEnum, required=True)
    proximity_display = EnumDescription(source='get_proximity_display', required=True)
    unit_of_ananlysis = graphene.Field(UnitOfAnalysisTypeEnum, required=True)
    unit_of_analysis_display = EnumDescription(source='get_affected_groups_display', required=True)
    unit_of_reporting = graphene.Field(UnitOfReportingTypeEnum, required=True)
    unit_of_reporting_display = EnumDescription(source='get_unit_of_reporting_display', required=True)


class AdditionalDocumentType(DjangoObjectType, UserResourceMixin):
    class Meta:
        model = AdditionalDocument
        fields = ("id", "assessment_registry", "file", "external_link")

    document_type = graphene.Field(DocumentTypeEnum, required=True)
    document_type_display = EnumDescription(source='get_document_type_display', required=True)


class AssessmentRegistryType(
        DjangoObjectType,
        UserResourceMixin
):

    class Meta:
        model = AssessmentRegistry
        fields = (
            "id", "lead", "project", "lead_group", "bg_countries", "bg_crisis_start_date",
            "cost_estimates_usd", "no_of_pages", "data_collection_start_date", "data_collection_end_date",
            "publication_date", "lead_organizations", "international_partners", "donors", "national_partners",
            "governments", "objectives", "data_collection_techniques", "sampling", "limitations", "locations",
        )

    bg_crisis_type = graphene.Field(CrisisTypeEnum, required=True)
    bg_crisis_type_display = EnumDescription(source='get_bg_crisis_type_display', required=True)
    bg_preparedness = graphene.Field(PreparednessTypeEnum, required=True)
    bg_preparedness_display = EnumDescription(source='get_bg_preparedness_display', required=True)
    external_support = graphene.Field(ExternalSupportTypeEnum, required=True)
    external_support_display = EnumDescription(source='get_external_support_display', required=True)
    coordinated_joint = graphene.Field(CoordinationTypeEnum, required=True)
    coordinated_joint_display = EnumDescription(source='get_coordinated_joint_display', required=True)
    details_type = graphene.Field(DetailTypeEnum, required=True)
    details_type_display = EnumDescription(source='get_details_type_display', required=True)
    family = graphene.Field(FamilyTypeEnum, required=True)
    family_display = EnumDescription(source='get_family_display', required=True)
    frequency = graphene.Field(FrequencyTypeEnum, required=True)
    frequency_display = EnumDescription(source='get_frequency_display', required=True)
    confidentiality = graphene.Field(ConfidentialityTypeEnum, required=True)
    confidentiality_display = EnumDescription(source='get_confidentiality_display', required=True)
    language = graphene.List(graphene.NonNull(LanguageTypeEnum), required=True)
    focuses = graphene.List(graphene.NonNull(FocusTypeEnum), required=True)
    sectors = graphene.List(graphene.NonNull(SectorTypeEnum), required=True)
    protection_info_mgmts = graphene.List(graphene.NonNull(ProtectionInfoTypeEnum), required=True)
    affected_groups = graphene.Field(AffectedGroupTypeEnum, required=True)
    affected_groups_display = EnumDescription(source='get_affected_groups_display', required=True)
    methodology_attributes = graphene.List(graphene.NonNull(MethodologyAttributeType), required=False)
    additional_documents = graphene.List(graphene.NonNull(AdditionalDocumentType), required=False)
