import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

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
    Summary,
    SummarySubSectorIssue,
    SummaryIssue,
    SummaryFocus,
    SummaryFocusSubSectorIssue,
    ScoreRating,
    ScoreAnalyticalDensity,
    Question,
    Answer,
)
from .filters import AssessmentRegistryGQFilterSet, IssueGQFilterSet
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
    AssessmentRegistryCNAQuestionSectorTypeEnum,
    AssessmentRegistryCNAQuestionSubSectorTypeEnum,
    AssessmentRegistrySummarySectorTypeEnum,
    AssessmentRegistrySummarySubSectorTypeEnum,
    AssessmentRegistrySummaryFocusSectorTypeEnum,
    AssessmentRegistrySummaryFocusSubSectorTypeEnum,
)


class QuestionType(DjangoObjectType, UserResourceMixin):
    class Meta:
        model = Question
        fields = ("id", "question", "sub_sector",)

    sector = graphene.Field(AssessmentRegistryCNAQuestionSectorTypeEnum, required=False)
    sector_display = EnumDescription(source='get_sector_display', required=False)

    sub_sector = graphene.Field(AssessmentRegistryCNAQuestionSubSectorTypeEnum, required=False)
    sub_sector_display = EnumDescription(source='get_sub_sector_display', required=False)


class SummarySubSectorType(graphene.ObjectType):
    sub_sector = graphene.String()
    sub_sector_value = graphene.Int()


class SummaryOptionType(graphene.ObjectType):
    sector = graphene.Field(AssessmentRegistrySummarySectorTypeEnum, required=False)
    sub_sector = graphene.List(AssessmentRegistrySummarySubSectorTypeEnum, required=False)


class SummaryFocusOptionType(graphene.ObjectType):
    sector = graphene.Field(AssessmentRegistrySummaryFocusSectorTypeEnum, required=False)
    sub_sector = graphene.List(AssessmentRegistrySummaryFocusSubSectorTypeEnum, required=False)


class AssessmentRegistryOptionsType(graphene.ObjectType):
    cna_questions = graphene.List(graphene.NonNull(QuestionType), required=False)
    summary_options = graphene.List(SummaryOptionType)
    summary_focus_options = graphene.List(SummaryFocusOptionType)

    @staticmethod
    def resolve_cna_questions(root, info, **kwargs):
        return Question.objects.all()

    @staticmethod
    def resolve_summary_options(root, info, **kwargs):
        return [
            SummaryOptionType(
                sector=enum,
                sub_sector=[
                    enum for enum, _ in SummaryIssue.SubSector.choices if 0 <= enum <= 5
                ]
            ) for enum, _ in Summary.Sector.choices if enum == 0
        ] + [
            SummaryOptionType(
                sector=enum,
                sub_sector=[
                    enum for enum, _ in SummaryIssue.SubSector.choices if 6 <= enum <= 9
                ]
            ) for enum, _ in Summary.Sector.choices if enum == 1
        ] + [
            SummaryOptionType(
                sector=enum,
                sub_sector=[
                    enum for enum, _ in SummaryIssue.SubSector.choices if 10 <= enum <= 14
                ]
            ) for enum, _ in Summary.Sector.choices if enum == 2
        ] + [
            SummaryOptionType(
                sector=enum,
                sub_sector=[
                    enum for enum, _ in SummaryIssue.SubSector.choices if 15 <= enum <= 18
                ]
            ) for enum, _ in Summary.Sector.choices if enum == 3
        ] + [
            SummaryOptionType(
                sector=enum,
                sub_sector=[
                    enum for enum, _ in SummaryIssue.SubSector.choices if 19 <= enum <= 21
                ]
            ) for enum, _ in Summary.Sector.choices if enum == 4
        ]

    @staticmethod
    def resolve_summary_focus_options(root, info, **kwargs):
        return [
            SummaryFocusOptionType(
                sector=enum,
                sub_sector=[
                    enum for enum, _ in SummaryIssue.SubSector.choices if 0 <= enum <= 2
                ]
            ) for enum, _ in Summary.Sector.choices if enum == 0
        ] + [
            SummaryFocusOptionType(
                sector=enum,
                sub_sector=[
                    enum for enum, _ in SummaryIssue.SubSector.choices if 3 <= enum <= 5
                ]
            ) for enum, _ in Summary.Sector.choices if enum == 1
        ] + [
            SummaryFocusOptionType(
                sector=enum,
                sub_sector=[
                    enum for enum, _ in SummaryIssue.SubSector.choices if 6 <= enum <= 9
                ]
            ) for enum, _ in Summary.Sector.choices if enum == 2
        ] + [
            SummaryFocusOptionType(
                sector=enum,
                sub_sector=[
                    enum for enum, _ in SummaryIssue.SubSector.choices if 10 <= enum <= 14
                ]
            ) for enum, _ in Summary.Sector.choices if enum == 3
        ]


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
        return assessment_registry_qs.filter(confidentiality=AssessmentRegistry.ConfidentialityType.UNPROTECTED)
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


class IssueType(DjangoObjectType, UserResourceMixin):
    sub_sector = graphene.Field(AssessmentRegistrySummarySubSectorTypeEnum, required=False)
    sub_sector_display = graphene.String(required=False)
    focus_sub_sector = graphene.Field(AssessmentRegistrySummaryFocusSubSectorTypeEnum, required=False)
    focus_sub_sector_display = graphene.String(required=False)

    class Meta:
        model = SummaryIssue
        fields = [
            'id', 'parent', 'label', 'full_label',
        ]

    @staticmethod
    def resolve_sub_sector_display(root, info, **kwargs):
        if root.sub_sector is not None:
            return root.get_sub_sector_display()
        return None

    @staticmethod
    def resolve_focus_sub_sector_display(root, info, **kwargs):
        if root.focus_sub_sector is not None:
            return root.get_focus_sub_sector_display()
        return None


class IssueListType(CustomDjangoListObjectType):
    class Meta:
        model = SummaryIssue
        filterset_class = IssueGQFilterSet


class SummaryType(DjangoObjectType, UserResourceMixin):
    class Meta:
        model = Summary
        fields = [
            "id", "total_people_assessed", "total_dead", "total_injured", "total_missing",
            "total_people_facing_hum_access_cons", "percentage_of_people_facing_hum_access_cons",
        ]


class SummarySubSectorIssueType(DjangoObjectType, UserResourceMixin):
    issue = graphene.Field(IssueType, required=False)

    class Meta:
        model = SummarySubSectorIssue
        fields = [
            "id", "text", "order", "lead_preview_text_ref"
        ]

    @staticmethod
    def resolve_issue(root, info, **kwargs):
        return root.summary_issue


class SummaryFocusType(DjangoObjectType, UserResourceMixin):
    class Meta:
        model = SummaryFocus


class SummaryFocusSubSectorIssueType(DjangoObjectType, UserResourceMixin):
    focus = graphene.Field(AssessmentRegistryFocusTypeEnum, required=False)
    focus_display = graphene.String(required=False)

    class Meta:
        model = SummaryFocusSubSectorIssue


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
    summary_meta = graphene.Field(SummaryType, required=False)
    summary_subsector_issue = graphene.List(SummarySubSectorIssueType, required=False)
    summary_focus_meta = graphene.List(SummaryFocusType, required=False)
    summary_focus_subsector_issue = graphene.List(SummaryFocusSubSectorIssueType, required=False)

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
    def resolve_cna(root, info, **kwargs):
        return Answer.objects.filter(assessment_registry=root)

    @staticmethod
    def resolve_summary_meta(root, info, **kwargs):
        return Summary.objects.get(assessment_registry=root)

    @staticmethod
    def resolve_summary_subsector_issue(root, info, **kwargs):
        return SummarySubSectorIssue.objects.filter(assessment_registry=root)

    @staticmethod
    def resolve_summary_focus_meta(root, info, **kwargs):
        return SummaryFocus.objects.filter(assessment_registry=root)

    @staticmethod
    def resolve_summary_focus_subsector_issue(root, info, **kwargs):
        return SummaryFocusSubSectorIssue.objects.filter(assessment_registry=root)


class AssessmentRegistryListType(CustomDjangoListObjectType):
    class Meta:
        model = AssessmentRegistry
        filterset_class = AssessmentRegistryGQFilterSet


class ProjectQuery:
    assessment_registry = DjangoObjectField(AssessmentRegistryType)
    assessment_registries = DjangoPaginatedListObjectField(
        AssessmentRegistryListType,
        pagination=NoOrderingPageGraphqlPagination(
            page_size_query_param='pageSize',
        )
    )
    assessment_registry_options = graphene.Field(AssessmentRegistryOptionsType)

    @staticmethod
    def resolve_assessment_registries(root, info, **kwargs):
        return get_assessment_registry_qs(info)

    @staticmethod
    def resolve_assessment_registry_options(root, info, **kwargs):
        return AssessmentRegistryOptionsType


class Query():
    issue = DjangoObjectField(IssueType)
    issues = DjangoPaginatedListObjectField(
        IssueListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
