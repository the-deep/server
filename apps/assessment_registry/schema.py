import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField

from utils.graphene.types import ClientIdMixin, CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import NoOrderingPageGraphqlPagination
from utils.graphene.enums import EnumDescription
from deep.permissions import ProjectPermissions as PP
from user_resource.schema import UserResourceMixin
from lead.schema import LeadDetailType

from .models import (
    AssessmentRegistry,
    MethodologyAttribute,
    AdditionalDocument,
    ScoreRating,
    ScoreAnalyticalDensity,
    Summary,
)
from .filters import AssessmentRegistryGQFilterSet
from .enums import (
    AssessmentRegistryCrisisTypeEnum,
    AssessmentRegistryPreparednessTypeEnum,
    AssessmentRegistryExternalSupportTypeEnum,
    AssessmentRegistryCoordinationTypeEnum,
    AssessmentRegistryDetailTypeEnum,
    AssessmentRegistryFamilyTypeEnum,
    AssessmentRegistryFrequencyTypeEnum,
    AssessmentRegistryConfidentialityTypeEnum,
    AssessmentRegistryLanguageTypeEnum,
    AssessmentRegistryFocusTypeEnum,
    AssessmentRegistrySectorTypeEnum,
    AssessmentRegistryProtectionInfoTypeEnum,
    AssessmentRegistryAffectedGroupTypeEnum,
    AssessmentRegistryDataCollectionTechniqueTypeEnum,
    AssessmentRegistrySamplingApproachTypeEnum,
    AssessmentRegistryProximityTypeEnum,
    AssessmentRegistryUnitOfAnalysisTypeEnum,
    AssessmentRegistryUnitOfReportingTypeEnum,
    AssessmentRegistryDocumentTypeEnum,
    AssessmentRegistryScoreTypeEnum,
    AssessmentRegistryRatingTypeEnum,
)


class SummaryValueChoiceType(graphene.ObjectType):
    value_name = graphene.String(required=False)
    value = graphene.Int(required=False)


class SummarySubSectorType(graphene.ObjectType):
    sub_sector_name = graphene.String(required=False)
    sub_sector_value = graphene.Int(required=False)
    value_type = graphene.String(required=False)
    value_type_value = graphene.Int(required=False)
    value_choices = graphene.List(SummaryValueChoiceType, required=False)


class SummaryColumnType(graphene.ObjectType):
    col_name = graphene.String(required=False)
    col_value = graphene.Int(required=False)


class SummaryRowType(graphene.ObjectType):
    row_name = graphene.String(required=False)
    row_value = graphene.Int(required=False)


class SummarySectorOptionType(graphene.ObjectType):
    sub_sector = graphene.List(graphene.NonNull(SummarySubSectorType))
    columns = graphene.List(graphene.NonNull(SummaryColumnType))
    rows = graphene.List(graphene.NonNull(SummaryRowType))

    @staticmethod
    def resolve_sub_sector(root, info, **kwargs):
        return [
            SummarySubSectorType(
                sub_sector_name=value,
                sub_sector_value=key,
                value_type=Summary.ValueType.ENUM.label,
                value_type_value=Summary.ValueType.ENUM,
                value_choices=[
                    SummaryValueChoiceType(
                        value_name=value,
                        value=key
                    ) for key, value in Summary.SummarySectorValue.choices if 52 <= key <= 63
                ]
            ) for key, value in Summary.SubSector.choices if key == 0
        ] + [
            SummarySubSectorType(
                sub_sector_name=value,
                sub_sector_value=key,
                value_type=Summary.ValueType.RAW.label,
                value_type_value=Summary.ValueType.RAW,
                value_choices=[],
            ) for key, value in Summary.SubSector.choices if key == 1
        ]

    @staticmethod
    def resolve_columns(root, info, **kwargs):
        return [
            SummaryColumnType(
                col_name=value,
                col_value=key
            ) for key, value in Summary.SectorColumn.choices
        ]

    @staticmethod
    def resolve_rows(root, info, **kwargs):
        return [
            SummaryRowType(
                row_name=value,
                row_value=key
            ) for key, value in Summary.Row.choices
        ]


class SummarySubFocusType(graphene.ObjectType):
    sub_focus_name = graphene.String(required=False)
    sub_focus_value = graphene.Int(required=False)
    value_type = graphene.String(required=False)
    value_type_value = graphene.Int(required=False)
    value_choices = graphene.List(SummaryValueChoiceType, required=False)


class SummaryFocusOptionType(graphene.ObjectType):
    sub_focus = graphene.List(graphene.NonNull(SummarySubFocusType))
    columns = graphene.List(graphene.NonNull(SummaryColumnType))
    rows = graphene.List(graphene.NonNull(SummaryRowType))

    @staticmethod
    def resolve_sub_focus(root, info, **kwargs):
        return [
            SummarySubFocusType(
                sub_focus_name=value,
                sub_focus_value=key,
                value_type=Summary.ValueType.RAW.label,
                value_type_value=Summary.ValueType.RAW,
                value_choices=[]
            ) for key, value in Summary.SubFocus.choices if key == 0
        ] + [
            SummarySubFocusType(
                sub_focus_name=value,
                sub_focus_value=key,
                value_type=Summary.ValueType.ENUM.label,
                value_type_value=Summary.ValueType.ENUM,
                value_choices=[
                    SummaryValueChoiceType(
                        value_name=value,
                        value=key
                    ) for key, value in Summary.SummaryFocusValue.choices if 0 <= key <= 23
                ]
            ) for key, value in Summary.SubFocus.choices if key == 1
        ] + [
            SummarySubFocusType(
                sub_focus_name=value,
                sub_focus_value=key,
                value_type=Summary.ValueType.ENUM.label,
                value_type_value=Summary.ValueType.ENUM,
                value_choices=[
                    SummaryValueChoiceType(
                        value_name=value,
                        value=key
                    ) for key, value in Summary.SummaryFocusValue.choices if 24 <= key <= 40
                ]

            ) for key, value in Summary.SubFocus.choices if key == 2
        ] + [
            SummarySubFocusType(
                sub_focus_name=value,
                sub_focus_value=key,
                value_type=Summary.ValueType.ENUM.label,
                value_type_value=Summary.ValueType.ENUM,
                value_choices=[
                    SummaryValueChoiceType(
                        value_name=value,
                        value=key
                    ) for key, value in Summary.SummaryFocusValue.choices if 41 <= key <= 51
                ]

            ) for key, value in Summary.SubFocus.choices if key == 3
        ]

    @staticmethod
    def resolve_columns(root, info, **kwargs):
        return [
            SummaryColumnType(
                col_name=value,
                col_value=key
            ) for key, value in Summary.FocusColumn.choices
        ]

    @staticmethod
    def resolve_rows(root, info, **kwargs):
        return [
            SummaryRowType(
                row_name=value,
                row_value=key
            ) for key, value in Summary.Row.choices
        ]


class AssessmentRegistryOptionsType(graphene.ObjectType):
    summary_sector = graphene.Field(SummarySectorOptionType)
    summary_focus = graphene.Field(SummaryFocusOptionType)

    @staticmethod
    def resolve_summary_sector(root, info, **kwargs):
        return SummarySectorOptionType

    @staticmethod
    def resolve_summary_focus(root, info, **kwargs):
        return SummaryFocusOptionType


class ScoreRatingType(DjangoObjectType, UserResourceMixin):
    class Meta:
        model = ScoreRating
        fields = ("id", "client_id", "score_type", "rating", "reason",)

    score_type = graphene.Field(AssessmentRegistryScoreTypeEnum, required=True)
    score_type_display = EnumDescription(source='get_score_type_display', required=True)
    rating = graphene.Field(AssessmentRegistryRatingTypeEnum, required=True)
    rating_display = EnumDescription(source='get_rating_display', required=True)


class ScoreAnalyticalDensityType(DjangoObjectType, UserResourceMixin):
    class Meta:
        model = ScoreAnalyticalDensity
        fields = ("id", "client_id", "sector", "value")

    sector = graphene.Field(AssessmentRegistrySectorTypeEnum, required=True)
    sector_display = EnumDescription(source='get_sector_display', required=True)


def get_assessment_registry_qs(info):
    assessment_registry_qs = AssessmentRegistry.objects.filter(project=info.context.active_project)
    # Generate queryset according to permission
    if PP.check_permission(info, PP.Permission.VIEW_ALL_LEAD):
        return assessment_registry_qs
    elif PP.check_permission(info, PP.Permission.VIEW_ONLY_UNPROTECTED_LEAD):
        return assessment_registry_qs.filter(confidentiality=AssessmentRegistry.Confidentiality.UNPROTECTED)
    return AssessmentRegistry.objects.none()


class MethodologyAttributeType(DjangoObjectType, UserResourceMixin):
    class Meta:
        model = MethodologyAttribute
        fields = ("id", "client_id", "proximity",)

    data_collection_technique = graphene.Field(AssessmentRegistryDataCollectionTechniqueTypeEnum, required=True)
    data_collection_technique_display = EnumDescription(source='get_data_collection_technique_display', required=True)
    sampling_approach = graphene.Field(AssessmentRegistrySamplingApproachTypeEnum, required=True)
    sampling_appraoch_display = EnumDescription(source='get_sampling_approach_display', required=True)
    proximity = graphene.Field(AssessmentRegistryProximityTypeEnum, required=True)
    proximity_display = EnumDescription(source='get_proximity_display', required=True)
    unit_of_analysis = graphene.Field(AssessmentRegistryUnitOfAnalysisTypeEnum, required=True)
    unit_of_analysis_display = EnumDescription(source='get_unit_of_analysis_display', required=True)
    unit_of_reporting = graphene.Field(AssessmentRegistryUnitOfReportingTypeEnum, required=True)
    unit_of_reporting_display = EnumDescription(source='get_unit_of_reporting_display', required=True)


class AdditionalDocumentType(DjangoObjectType, UserResourceMixin):
    class Meta:
        model = AdditionalDocument
        fields = ("id", "client_id", "file", "external_link")

    document_type = graphene.Field(AssessmentRegistryDocumentTypeEnum, required=True)
    document_type_display = EnumDescription(source='get_document_type_display', required=True)


class AssessmentRegistryType(
        DjangoObjectType,
        UserResourceMixin,
        ClientIdMixin,
):

    class Meta:
        model = AssessmentRegistry
        fields = (
            "id", "lead", "project", "bg_countries", "bg_crisis_start_date",
            "cost_estimates_usd", "no_of_pages", "data_collection_start_date", "data_collection_end_date",
            "publication_date", "lead_organizations", "international_partners", "donors", "national_partners",
            "governments", "objectives", "data_collection_techniques", "sampling", "limitations", "locations",
            "matrix_score", "final_score",
        )

    bg_crisis_type = graphene.Field(AssessmentRegistryCrisisTypeEnum, required=True)
    bg_crisis_type_display = EnumDescription(source='get_bg_crisis_type_display', required=True)
    bg_preparedness = graphene.Field(AssessmentRegistryPreparednessTypeEnum, required=True)
    bg_preparedness_display = EnumDescription(source='get_bg_preparedness_display', required=True)
    external_support = graphene.Field(AssessmentRegistryExternalSupportTypeEnum, required=True)
    external_support_display = EnumDescription(source='get_external_support_display', required=True)
    coordinated_joint = graphene.Field(AssessmentRegistryCoordinationTypeEnum, required=True)
    coordinated_joint_display = EnumDescription(source='get_coordinated_joint_display', required=True)
    details_type = graphene.Field(AssessmentRegistryDetailTypeEnum, required=True)
    details_type_display = EnumDescription(source='get_details_type_display', required=True)
    family = graphene.Field(AssessmentRegistryFamilyTypeEnum, required=True)
    family_display = EnumDescription(source='get_family_display', required=True)
    frequency = graphene.Field(AssessmentRegistryFrequencyTypeEnum, required=True)
    frequency_display = EnumDescription(source='get_frequency_display', required=True)
    confidentiality = graphene.Field(AssessmentRegistryConfidentialityTypeEnum, required=True)
    confidentiality_display = EnumDescription(source='get_confidentiality_display', required=True)
    language = graphene.List(graphene.NonNull(AssessmentRegistryLanguageTypeEnum), required=True)
    focuses = graphene.List(graphene.NonNull(AssessmentRegistryFocusTypeEnum), required=True)
    sectors = graphene.List(graphene.NonNull(AssessmentRegistrySectorTypeEnum), required=True)
    protection_info_mgmts = graphene.List(graphene.NonNull(AssessmentRegistryProtectionInfoTypeEnum), required=True)
    affected_groups = graphene.Field(AssessmentRegistryAffectedGroupTypeEnum, required=True)
    affected_groups_display = EnumDescription(source='get_affected_groups_display', required=True)
    methodology_attributes = graphene.List(graphene.NonNull(MethodologyAttributeType), required=False)
    additional_documents = graphene.List(graphene.NonNull(AdditionalDocumentType), required=False)
    score_ratings = graphene.List(graphene.NonNull(ScoreRatingType), required=True)
    score_analytical_density = graphene.List(graphene.NonNull(ScoreAnalyticalDensityType), required=True)
    lead = graphene.NonNull(LeadDetailType)

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_assessment_registry_qs(info)

    @staticmethod
    def resolve_methodology_attributes(root, info, **kwargs):
        return MethodologyAttribute.objects.filter(assessment_registry=root)

    @staticmethod
    def resolve_additional_documents(root, info, **kwargs):
        return AdditionalDocument.objects.filter(assessment_registry=root)

    @staticmethod
    def resolve_score_ratings(root, info, **kwargs):
        return ScoreRating.objects.filter(assessment_registry=root)

    @staticmethod
    def resolve_score_analytical_density(root, info, **kwargs):
        return ScoreAnalyticalDensity.objects.filter(assessment_registry=root)


class AssessmentRegistryListType(CustomDjangoListObjectType):
    class Meta:
        model = AssessmentRegistry
        filterset_class = AssessmentRegistryGQFilterSet


class Query:
    assessment_registry = DjangoObjectField(AssessmentRegistryType)
    assessment_registries = DjangoPaginatedListObjectField(
        AssessmentRegistryListType,
        pagination=NoOrderingPageGraphqlPagination(
            page_size_query_param='pageSize',
        )
    )
    assessment_reg_options = graphene.Field(AssessmentRegistryOptionsType)

    @staticmethod
    def resolve_assessment_reg_options(root, info, **kwargs):
        return AssessmentRegistryOptionsType
