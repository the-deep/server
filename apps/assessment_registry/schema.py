import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField

from utils.common import render_string_for_graphql
from utils.graphene.types import ClientIdMixin, CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import NoOrderingPageGraphqlPagination
from utils.graphene.enums import EnumDescription
from deep.permissions import ProjectPermissions as PP
from user_resource.schema import UserResourceMixin
from lead.schema import LeadDetailType
from geo.schema import ProjectGeoAreaType

from .models import (
    AssessmentRegistry,
    MethodologyAttribute,
    AdditionalDocument,
    ScoreRating,
    ScoreAnalyticalDensity,
    Summary,
    Question,
    Answer,
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
    AssessmentRegistrySummaryValueTypeEnum,
    AssessmentRegistrySummaryRowTypeEnum,
    AssessmentRegistrySummarySectorColumnTypeEnum,
    AssessmentRegistrySummaryFocusColumnTypeEnum,
    AssessmentRegistrySummarySubSectorTypeEnum,
    AssessmentRegistrySummarySubFocusTypeEnum,
    AssessmentRegistrySummaryFocusTypeEnum,
    AssessmentRegistrySummarySectorTypeEnum,
    AssessmentRegistrySummaryFocusValueTypeEnum,
    AssessmentRegistrySummarySectorValueTypeEnum,
    AssessmentRegistryCNAQuestionSectorTypeEnum,
    AssessmentRegistryCNAQuestionSubSectorTypeEnum,
)


# NOTE : Summary data is aspected to merge with information tab data so, some changes may come to summary types
def get_summary_sub_focus_value():
        SummarySubFocusType(
            sub_focus_name=value,
            sub_focus_name_display=label,
            sub_focus_name_value=value,
            summary_value_type=Summary.ValueType.RAW,
            summary_value_type_display=AssessmentRegistrySummaryValueTypeEnum.RAW.label,
            value_choices=[]
        ) for value, label in Summary.SubFocus.choices if value == 0
    ] + [
        SummarySubFocusType(
            sub_focus_name=value,
            sub_focus_name_display=label,
            sub_focus_name_value=value,
            summary_value_type=Summary.ValueType.ENUM,
            summary_value_type_display=AssessmentRegistrySummaryValueTypeEnum.ENUM.label,
            value_choices=[
                SummaryValueChoiceType(
                    value_name=value,
                    value=key
                ) for key, value in Summary.SummaryFocusValue.choices if 100 <= key < 200
            ]
        ) for value, label in Summary.SubFocus.choices if value == 1
    ] + [
        SummarySubFocusType(
            sub_focus_name=value,
            sub_focus_name_display=label,
            sub_focus_name_value=value,
            summary_value_type=Summary.ValueType.ENUM,
            summary_value_type_display=AssessmentRegistrySummaryValueTypeEnum.ENUM.label,
            value_choices=[
                SummaryValueChoiceType(
                    value_name=value,
                    value=key
                ) for key, value in Summary.SummaryFocusValue.choices if 200 <= key < 300
            ]

        ) for value, label in Summary.SubFocus.choices if value == 2
    ] + [
        SummarySubFocusType(
            sub_focus_name=value,
            sub_focus_name_display=label,
            sub_focus_name_value=value,
            summary_value_type=Summary.ValueType.ENUM,
            summary_value_type_display=AssessmentRegistrySummaryValueTypeEnum.ENUM.label,
            value_choices=[
                SummaryValueChoiceType(
                    value_name=value,
                    value=key
                ) for key, value in Summary.SummaryFocusValue.choices if 300 <= key < 400
            ]

        ) for value, label in Summary.SubFocus.choices if value == 3
    ]


def get_summary_sub_sector_value():
    return [
        SummarySubSectorType(
            sub_sector_name=value,
            sub_sector_name_display=label,
            sub_sector_name_value=value,
            summary_value_type=Summary.ValueType.ENUM,
            summary_value_type_display=AssessmentRegistrySummaryValueTypeEnum.ENUM.label,
            value_choices=[
                SummaryValueChoiceType(
                    value_name=value,
                    value=key
                ) for key, value in Summary.SummarySectorValue.choices if 400 <= key < 500
            ]
        ) for value, label in Summary.SubSector.choices if value == 0
    ] + [
        SummarySubSectorType(
            sub_sector_name=value,
            sub_sector_name_display=label,
            sub_sector_name_value=value,
            summary_value_type=Summary.ValueType.RAW,
            summary_value_type_display=AssessmentRegistrySummaryValueTypeEnum.RAW.label,
            value_choices=[],
        ) for value, label in Summary.SubSector.choices if value == 1
    ]


class SummaryValueChoiceType(graphene.ObjectType):


class SummaryFocusDataType(graphene.ObjectType):
    sub_focus = graphene.Field(AssessmentRegistrySummarySubFocusTypeEnum, required=False)
    column = graphene.Field(AssessmentRegistrySummaryFocusColumnTypeEnum, required=False)
    row = graphene.Field(AssessmentRegistrySummaryRowTypeEnum, required=False)
    value = graphene.Field(AssessmentRegistrySummaryFocusValueTypeEnum, required=False)
    raw_value = graphene.String(required=False)


class SummarySectorDataType(graphene.ObjectType):
    sub_sector = graphene.Field(AssessmentRegistrySummarySubSectorTypeEnum, required=False)
    column = graphene.Field(AssessmentRegistrySummarySectorColumnTypeEnum, required=False)
    row = graphene.Field(AssessmentRegistrySummaryRowTypeEnum, required=False)
    value = graphene.Field(AssessmentRegistrySummarySectorValueTypeEnum, required=False)
    raw_value = graphene.String(required=False)


class SummaryType(DjangoObjectType, UserResourceMixin):
    class Meta:
        model = Summary
        fields = ("id", "client_id", "sector_data")

    focus_data = graphene.List(SummaryFocusDataType, required=False)
    sector_data = graphene.List(SummarySectorDataType, required=False)
    summary_focus = graphene.Field(AssessmentRegistrySummaryFocusTypeEnum, required=False)
    summary_focus_display = EnumDescription(source='get_summary_focus_display', required=False)
    summary_sector = graphene.Field(AssessmentRegistrySummarySectorTypeEnum, required=False)
    summary_sector_display = EnumDescription(source='get_summary_sector_display', required=False)


class SummarySubSectorType(graphene.ObjectType):
    sub_sector_name = graphene.Field(AssessmentRegistrySummarySubSectorTypeEnum, required=False)
    sub_sector_name_display = graphene.String(required=False)
    sub_sector_name_value = graphene.Int(required=False)
    value_choices = graphene.List(SummaryValueChoiceType, required=False)
    summary_value_type = graphene.Field(AssessmentRegistrySummaryValueTypeEnum)
    summary_value_type_display = graphene.String(required=False)


class SummarySectorColumnType(graphene.ObjectType):
    col_name = graphene.Field(AssessmentRegistrySummarySectorColumnTypeEnum, required=False)
    col_name_display = graphene.String(required=False)


class SummaryRowType(graphene.ObjectType):
    row_name = graphene.Field(AssessmentRegistrySummaryRowTypeEnum, required=False)
    row_name_display = graphene.String(required=False)


class SummarySectorOptionType(graphene.ObjectType):
    sub_sector = graphene.List(graphene.NonNull(SummarySubSectorType))
    columns = graphene.List(graphene.NonNull(SummarySectorColumnType))
    rows = graphene.List(graphene.NonNull(SummaryRowType))

    @staticmethod
    def resolve_sub_sector(root, info, **kwargs):
        return get_summary_sub_sector_value()

    @staticmethod
    def resolve_columns(root, info, **kwargs):
        return [
            SummarySectorColumnType(
                col_name=value,
                col_name_display=label
            ) for value, label in Summary.SectorColumn.choices
        ]

    @staticmethod
    def resolve_rows(root, info, **kwargs):
        return [
            SummaryRowType(
                row_name=value,
                row_name_display=label,
            ) for value, label in Summary.Row.choices
        ]


class SummaryFocusColumnType(graphene.ObjectType):
    col_name = graphene.Field(AssessmentRegistrySummaryFocusColumnTypeEnum, required=False)
    col_name_display = graphene.String(required=False)


class SummarySubFocusType(graphene.ObjectType):
    sub_focus_name = graphene.Field(AssessmentRegistrySummarySubFocusTypeEnum, required=False)
    sub_focus_name_display = graphene.String(required=False)
    sub_focus_name_value = graphene.Int(required=False)
    value_choices = graphene.List(SummaryValueChoiceType, required=False)
    summary_value_type = graphene.Field(AssessmentRegistrySummaryValueTypeEnum, required=False)
    summary_value_type_display = graphene.String(required=False)


class SummaryFocusOptionType(graphene.ObjectType):
    sub_focus = graphene.List(graphene.NonNull(SummarySubFocusType))
    columns = graphene.List(graphene.NonNull(SummaryFocusColumnType))
    rows = graphene.List(graphene.NonNull(SummaryRowType))

    @staticmethod
    def resolve_sub_focus(root, info, **kwargs):
        return get_summary_sub_focus_value()

    @staticmethod
    def resolve_columns(root, info, **kwargs):
        return [
            SummaryFocusColumnType(
                col_name=value,
                col_name_display=label
            ) for value, label in Summary.FocusColumn.choices
        ]

    @staticmethod
    def resolve_rows(root, info, **kwargs):
        return [
            SummaryRowType(
                row_name=value,
                row_name_display=label
            ) for value, label in Summary.Row.choices
        ]


class QuestionType(DjangoObjectType, UserResourceMixin):
    class Meta:
        model = Question
        fields = ("id", "question", "sub_sector",)

    sector = graphene.Field(AssessmentRegistryCNAQuestionSectorTypeEnum, required=False)
    sector_display = EnumDescription(source='get_sector_display', required=False)

    sub_sector = graphene.Field(AssessmentRegistryCNAQuestionSubSectorTypeEnum, required=False)
    sub_sector_display = EnumDescription(source='get_sub_sector_display', required=False)


class AssessmentRegistryOptionsType(graphene.ObjectType):
    summary_sector = graphene.Field(SummarySectorOptionType)
    summary_focus = graphene.Field(SummaryFocusOptionType)
    cna_questions = graphene.List(graphene.NonNull(QuestionType), required=False)

    @staticmethod
    def resolve_summary_sector(root, info, **kwargs):
        return SummarySectorOptionType

    @staticmethod
    def resolve_summary_focus(root, info, **kwargs):
        return SummaryFocusOptionType

    @staticmethod
    def resolve_cna_questions(root, info, **kwargs):
        return Question.objects.all()


class ScoreRatingType(DjangoObjectType, UserResourceMixin, ClientIdMixin):
    class Meta:
        model = ScoreRating
        fields = ("id", "score_type", "rating", "reason",)

    score_type = graphene.Field(AssessmentRegistryScoreTypeEnum, required=True)
    score_type_display = EnumDescription(source='get_score_type_display', required=True)
    rating = graphene.Field(AssessmentRegistryRatingTypeEnum, required=True)
    rating_display = EnumDescription(source='get_rating_display', required=True)


class ScoreAnalyticalDensityType(DjangoObjectType, UserResourceMixin, ClientIdMixin):
    class Meta:
        model = ScoreAnalyticalDensity
        fields = ("id", "sector", "value")

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


class MethodologyAttributeType(DjangoObjectType, UserResourceMixin, ClientIdMixin):
    class Meta:
        model = MethodologyAttribute
        fields = ("id", "proximity", "sampling_size",)

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


class AdditionalDocumentType(DjangoObjectType, UserResourceMixin, ClientIdMixin):
    class Meta:
        model = AdditionalDocument
        fields = ("id", "file")

    document_type = graphene.Field(AssessmentRegistryDocumentTypeEnum, required=True)
    document_type_display = EnumDescription(source='get_document_type_display', required=True)
    external_link = graphene.String(required=False)

    def resolve_external_link(root, info, **kwargs):
        return render_string_for_graphql(root.external_link)


class CNAType(DjangoObjectType, UserResourceMixin):
    question = graphene.Field(QuestionType, required=False)

    class Meta:
        model = Answer
        fields = ("id", "question", "answer",)


class AssessmentRegistryType(
        DjangoObjectType,
        UserResourceMixin,
        ClientIdMixin,
):

    class Meta:
        model = AssessmentRegistry
        fields = (
            "id", "lead", "project", "bg_countries", "bg_crisis_start_date", "cost_estimates_usd", "no_of_pages",
            "data_collection_start_date", "data_collection_end_date", "publication_date", "executive_summary",
            "lead_organizations", "international_partners", "donors", "national_partners",
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
    affected_groups = graphene.List(graphene.NonNull(AssessmentRegistryAffectedGroupTypeEnum), required=True)
    methodology_attributes = graphene.List(graphene.NonNull(MethodologyAttributeType), required=False)
    additional_documents = graphene.List(graphene.NonNull(AdditionalDocumentType), required=False)
    score_ratings = graphene.List(graphene.NonNull(ScoreRatingType), required=True)
    score_analytical_density = graphene.List(graphene.NonNull(ScoreAnalyticalDensityType), required=True)
    lead = graphene.NonNull(LeadDetailType)
    locations = graphene.List(graphene.NonNull(ProjectGeoAreaType))
    summary = graphene.List(graphene.NonNull(SummaryType), required=False)
    cna = graphene.List(graphene.NonNull(CNAType), required=False)

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_assessment_registry_qs(info)

    @staticmethod
    def resolve_locations(root, info, **_):
        return info.context.dl.geo.assessment_registry_locations.load(root.pk)

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

    @staticmethod
    def resolve_summary(root, info, **kwargs):
        return Summary.objects.filter(assessment_registry=root)

    @staticmethod
    def resolve_cna(root, info, **kwargs):
        return Answer.objects.filter(assessment_registry=root)


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
    assessment_registry_options = graphene.Field(AssessmentRegistryOptionsType)

    @staticmethod
    def resolve_assessment_registry_options(root, info, **kwargs):
        return AssessmentRegistryOptionsType
