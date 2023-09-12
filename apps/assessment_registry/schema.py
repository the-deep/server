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
    SummarySubPillarIssue,
    SummaryIssue,
    SummaryFocus,
    SummarySubDimensionIssue,
    ScoreRating,
    ScoreAnalyticalDensity,
    Question,
    Answer,
    AssessmentRegistryOrganization,
)
from .filters import AssessmentRegistryGQFilterSet, AssessmentRegistryIssueGQFilterSet
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
    AssessmentRegistryScoreAnalyticalStatementTypeEnum,
    AssessmentRegistryScoreCriteriaTypeEnum,
    AssessmentRegistryRatingTypeEnum,
    AssessmentRegistryAnalysisLevelTypeEnum,
    AssessmentRegistryAnalysisFigureTypeEnum,
    AssessmentRegistryCNAQuestionSectorTypeEnum,
    AssessmentRegistryCNAQuestionSubSectorTypeEnum,
    AssessmentRegistrySummaryPillarTypeEnum,
    AssessmentRegistrySummarySubPillarTypeEnum,
    AssessmentRegistrySummaryFocusDimensionTypeEnum,
    AssessmentRegistrySummarySubDimensionTypeEnum,
    AssessmentRegistryOrganizationTypeEnum,
)


class AssessmentRegistryOrganizationType(DjangoObjectType, UserResourceMixin, ClientIdMixin):
    class Meta:
        model = AssessmentRegistryOrganization
        only_fields = (
            'id',
            'organization',
        )

    organization_type = graphene.Field(AssessmentRegistryOrganizationTypeEnum, required=True)
    organization_type_display = EnumDescription(source='get_organization_type_display', required=True)

    @staticmethod
    def resolve_organization(root, info):
        return info.context.dl.organization.organization.load(root.organization_id)


class QuestionType(DjangoObjectType, UserResourceMixin):
    class Meta:
        model = Question
        only_fields = (
            'id',
            'question',
        )

    sector = graphene.Field(AssessmentRegistryCNAQuestionSectorTypeEnum, required=False)
    sector_display = EnumDescription(source='get_sector_display', required=False)

    sub_sector = graphene.Field(AssessmentRegistryCNAQuestionSubSectorTypeEnum, required=False)
    sub_sector_display = EnumDescription(source='get_sub_sector_display', required=False)


class SummaryOptionType(graphene.ObjectType):
    pillar = graphene.Field(AssessmentRegistrySummaryPillarTypeEnum, required=True)
    pillar_display = EnumDescription(required=True)
    sub_pillar = graphene.Field(AssessmentRegistrySummarySubPillarTypeEnum, required=True)
    sub_pillar_display = EnumDescription(required=True)


class SummaryFocusOptionType(graphene.ObjectType):
    dimension = graphene.Field(AssessmentRegistrySummaryFocusDimensionTypeEnum, required=True)
    dimension_display = EnumDescription(required=True)
    sub_dimension = graphene.Field(AssessmentRegistrySummarySubDimensionTypeEnum, required=True)
    sub_dimension_display = EnumDescription(required=True)


class ScoreOptionsType(graphene.ObjectType):
    analytical_statement = graphene.Field(AssessmentRegistryScoreAnalyticalStatementTypeEnum, required=True)
    analytical_statement_display = EnumDescription(required=True)
    score_criteria = graphene.Field(AssessmentRegistryScoreCriteriaTypeEnum, required=True)
    score_criteria_display = EnumDescription(required=True)


class AssessmentRegistryOptionsType(graphene.ObjectType):
    cna_questions = graphene.List(graphene.NonNull(QuestionType), required=True)
    summary_options = graphene.List(graphene.NonNull(SummaryOptionType), required=True)
    summary_focus_options = graphene.List(graphene.NonNull(SummaryFocusOptionType), required=True)
    score_options = graphene.List(graphene.NonNull(ScoreOptionsType), required=True)

    @staticmethod
    def resolve_score_options(root, info, **kwargs):
        return [
            ScoreOptionsType(
                analytical_statement=statement.value,
                analytical_statement_display=statement.label,
                score_criteria=score_criteria.value,
                score_criteria_display=score_criteria.label,
            )
            for statement, score_criterias in ScoreRating.ANALYTICAL_STATEMENT_SCORE_CRITERIA_MAP.items()
            for score_criteria in score_criterias
        ]

    @staticmethod
    def resolve_summary_options(root, info, **kwargs):
        return [
            SummaryOptionType(
                pillar=pillar.value,
                pillar_display=pillar.label,
                sub_pillar=sub_pillar.value,
                sub_pillar_display=sub_pillar.label,
            )
            for pillar, sub_pillars in SummaryIssue.PILLAR_SUB_PILLAR_MAP.items()
            for sub_pillar in sub_pillars
        ]

    @staticmethod
    def resolve_summary_focus_options(root, info, **kwargs):
        return [
            SummaryFocusOptionType(
                dimension=dimension.value,
                dimension_display=dimension.label,
                sub_dimension=sub_dimension.value,
                sub_dimension_display=sub_dimension.label,
            )
            for dimension, sub_dimensions in SummaryIssue.DIMMENSION_SUB_DIMMENSION_MAP.items()
            for sub_dimension in sub_dimensions
        ]

    @staticmethod
    def resolve_cna_questions(root, info, **kwargs):
        return Question.objects.all()


class ScoreRatingType(DjangoObjectType, UserResourceMixin, ClientIdMixin):
    class Meta:
        model = ScoreRating
        only_fields = (
            'id',
            'reason',
        )

    score_type = graphene.Field(AssessmentRegistryScoreCriteriaTypeEnum, required=True)
    score_type_display = EnumDescription(source='get_score_type_display', required=True)
    rating = graphene.Field(AssessmentRegistryRatingTypeEnum, required=True)
    rating_display = EnumDescription(source='get_rating_display', required=True)


class ScoreAnalyticalDensityType(DjangoObjectType, UserResourceMixin, ClientIdMixin):
    class Meta:
        model = ScoreAnalyticalDensity
        only_fields = (
            'id',
        )

    sector = graphene.Field(AssessmentRegistrySectorTypeEnum, required=True)
    sector_display = EnumDescription(source='get_sector_display', required=True)
    analysis_level_covered = graphene.List(graphene.NonNull(AssessmentRegistryAnalysisLevelTypeEnum), required=True)
    figure_provided = graphene.List(graphene.NonNull(AssessmentRegistryAnalysisFigureTypeEnum), required=True)


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
        only_fields = (
            'id',
            'sampling_size',
        )

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
        only_fields = (
            'id',
            'file',
        )

    document_type = graphene.Field(AssessmentRegistryDocumentTypeEnum, required=True)
    document_type_display = EnumDescription(source='get_document_type_display', required=True)
    external_link = graphene.String(required=False)

    def resolve_external_link(root, info, **kwargs):
        return render_string_for_graphql(root.external_link)

    def resolve_file(root, info, **kwargs):
        if root.file_id:
            return info.context.dl.deep_gallery.file.load(root.file_id)


class CNAType(DjangoObjectType, UserResourceMixin, ClientIdMixin):
    question = graphene.Field(QuestionType, required=True)   # TODO: Dataloader

    class Meta:
        model = Answer
        only_fields = (
            'id',
            'question',
            'answer',
        )


class AssessmentRegistrySummaryIssueType(DjangoObjectType, UserResourceMixin):
    sub_pillar = graphene.Field(AssessmentRegistrySummarySubPillarTypeEnum, required=False)
    sub_pillar_display = EnumDescription(source='get_sub_pillar_display', required=False)
    sub_dimension = graphene.Field(AssessmentRegistrySummarySubDimensionTypeEnum, required=False)
    sub_dimension_display = EnumDescription(source='get_sub_dimension_display', required=False)

    class Meta:
        model = SummaryIssue
        only_fields = [
            'id',
            'parent',  # TODO: Dataloader
            'label',
            'full_label',
        ]


class AssessmentRegistrySummaryIssueListType(CustomDjangoListObjectType):
    class Meta:
        model = SummaryIssue
        filterset_class = AssessmentRegistryIssueGQFilterSet


class SummaryMetaType(DjangoObjectType, UserResourceMixin):
    class Meta:
        model = Summary
        only_fields = [
            'id',
            'total_people_assessed',
            'total_dead',
            'total_injured',
            'total_missing',
            'total_people_facing_hum_access_cons',
            'percentage_of_people_facing_hum_access_cons',
        ]


class SummarySubPillarIssueType(DjangoObjectType, UserResourceMixin, ClientIdMixin):
    class Meta:
        model = SummarySubPillarIssue
        only_fields = [
            'id',
            'text',
            'order',
            'summary_issue',
            'lead_preview_text_ref',
        ]

    @staticmethod
    def resolve_summary_issue(root, info, **kwargs):
        return info.context.dl.assessment_registry.issues.load(root.summary_issue_id)


class SummaryFocusMetaType(DjangoObjectType, UserResourceMixin, ClientIdMixin):
    sector = graphene.Field(AssessmentRegistrySectorTypeEnum, required=False)
    sector_display = EnumDescription(source='get_sector_display', required=False)

    class Meta:
        model = SummaryFocus
        only_fields = [
            'id',
            'percentage_of_people_affected',
            'total_people_affected',
            'percentage_of_moderate',
            'percentage_of_severe',
            'percentage_of_critical',
            'percentage_in_need',
            'total_moderate',
            'total_severe',
            'total_critical',
            'total_in_need',
            'total_pop_assessed',
            'total_not_affected',
            'total_affected',
            'total_people_in_need',
            'total_people_moderately_in_need',
            'total_people_severly_in_need',
            'total_people_critically_in_need',
        ]


class SummaryFocusSubDimensionIssueType(DjangoObjectType, UserResourceMixin, ClientIdMixin):
    sector = graphene.Field(AssessmentRegistrySectorTypeEnum, required=True)
    sector_display = EnumDescription(source='get_sector_display', required=True)

    class Meta:
        model = SummarySubDimensionIssue
        only_fields = [
            'id',
            'summary_issue',
            'text',
            'order',
            'lead_preview_text_ref',
        ]

    @staticmethod
    def resolve_summary_issue(root, info, **kwargs):
        return info.context.dl.assessment_registry.issues.load(root.summary_issue_id)


class AssessmentRegistryType(
        DjangoObjectType,
        UserResourceMixin,
        ClientIdMixin,
):
    class Meta:
        model = AssessmentRegistry
        only_fields = (
            'id',
            'bg_countries',
            'bg_crisis_start_date',
            'cost_estimates_usd',
            'no_of_pages',
            'data_collection_start_date',
            'data_collection_end_date',
            'publication_date',
            'executive_summary',
            'objectives',
            'data_collection_techniques',
            'sampling',
            'limitations',
            "metadata_complete",
            "additional_document_complete",
            "focus_complete",
            "methodology_complete",
            "summary_complete",
            "cna_complete",
            "score_complete"
        )

    # TODO: We might need to define dataloaders here for fields which are used for listing in client side

    project = graphene.ID(source='project_id', required=True)
    lead = graphene.NonNull(LeadDetailType)
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
    protection_info_mgmts = graphene.List(graphene.NonNull(AssessmentRegistryProtectionInfoTypeEnum), required=False)
    affected_groups = graphene.List(graphene.NonNull(AssessmentRegistryAffectedGroupTypeEnum), required=True)
    methodology_attributes = graphene.List(graphene.NonNull(MethodologyAttributeType), required=False)
    additional_documents = graphene.List(graphene.NonNull(AdditionalDocumentType), required=False)
    score_ratings = graphene.List(graphene.NonNull(ScoreRatingType), required=True)
    score_analytical_density = graphene.List(graphene.NonNull(ScoreAnalyticalDensityType), required=True)
    locations = graphene.List(graphene.NonNull(ProjectGeoAreaType))
    cna = graphene.List(graphene.NonNull(CNAType), required=False)
    summary_pillar_meta = graphene.Field(SummaryMetaType, required=False)
    summary_sub_pillar_issue = graphene.List(graphene.NonNull(SummarySubPillarIssueType), required=False)
    summary_dimension_meta = graphene.List(graphene.NonNull(SummaryFocusMetaType), required=False)
    summary_sub_dimension_issue = graphene.List(graphene.NonNull(SummaryFocusSubDimensionIssueType), required=False)
    lead = graphene.NonNull(LeadDetailType)
    stakeholders = graphene.List(graphene.NonNull(AssessmentRegistryOrganizationType))

    @staticmethod
    def resolve_stakeholders(root, info):
        return info.context.dl.assessment_registry.stakeholders.load(root.pk)

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
    def resolve_summary_pillar_meta(root, info, **kwargs):
        return Summary.objects.get(assessment_registry=root)

    @staticmethod
    def resolve_summary_sub_pillar_issue(root, info, **kwargs):
        return SummarySubPillarIssue.objects.filter(assessment_registry=root)

    @staticmethod
    def resolve_summary_dimension_meta(root, info, **kwargs):
        return SummaryFocus.objects.filter(assessment_registry=root)

    @staticmethod
    def resolve_summary_sub_dimension_issue(root, info, **kwargs):
        return SummarySubDimensionIssue.objects.filter(assessment_registry=root)


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
    assessment_reg_summary_issue = DjangoObjectField(AssessmentRegistrySummaryIssueType)
    assessment_reg_summary_issues = DjangoPaginatedListObjectField(
        AssessmentRegistrySummaryIssueListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
