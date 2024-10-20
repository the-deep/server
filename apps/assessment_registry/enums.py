from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import (
    AssessmentRegistry,
    MethodologyAttribute,
    AdditionalDocument,
    Summary,
    SummaryIssue,
    SummaryFocus,
    ScoreRating,
    ScoreAnalyticalDensity,
    Question,
    SummarySubDimensionIssue,
    AssessmentRegistryOrganization,
)


AssessmentRegistryCrisisTypeEnum = convert_enum_to_graphene_enum(
    AssessmentRegistry.CrisisType, name='AssessmentRegistryCrisisTypeEnum'
)
AssessmentRegistryPreparednessTypeEnum = convert_enum_to_graphene_enum(
    AssessmentRegistry.PreparednessType, name='AssessmentRegistryPreparednessTypeEnum'
)
AssessmentRegistryExternalSupportTypeEnum = convert_enum_to_graphene_enum(
    AssessmentRegistry.ExternalSupportType, name='AssessmentRegistryExternalTypeEnum'
)
AssessmentRegistryCoordinationTypeEnum = convert_enum_to_graphene_enum(
    AssessmentRegistry.CoordinationType, name='AssessmentRegistryCoordinationTypeEnum'
)
AssessmentRegistryDetailTypeEnum = convert_enum_to_graphene_enum(
    AssessmentRegistry.Type, name='AssessmentRegistryDetailTypeEnum'
)
AssessmentRegistryFamilyTypeEnum = convert_enum_to_graphene_enum(
    AssessmentRegistry.FamilyType, name='AssessmentRegistryFamilyTypeEnum'
)
AssessmentRegistryFrequencyTypeEnum = convert_enum_to_graphene_enum(
    AssessmentRegistry.FrequencyType, name='AssessmentRegistryFrequencyTypeEnum'
)
AssessmentRegistryConfidentialityTypeEnum = convert_enum_to_graphene_enum(
    AssessmentRegistry.ConfidentialityType, name='AssessmentRegistryConfidentialityTypeEnum'
)
AssessmentRegistryLanguageTypeEnum = convert_enum_to_graphene_enum(
    AssessmentRegistry.Language, name='AssessmentRegistryLanguageTypeEnum'
)
AssessmentRegistryFocusTypeEnum = convert_enum_to_graphene_enum(
    AssessmentRegistry.FocusType, name='AssessmentRegistryFocusTypeEnum'
)
AssessmentRegistrySectorTypeEnum = convert_enum_to_graphene_enum(
    AssessmentRegistry.SectorType, name='AssessmentRegistrySectorTypeEnum'
)
AssessmentRegistryProtectionInfoTypeEnum = convert_enum_to_graphene_enum(
    AssessmentRegistry.ProtectionInfoType, name='AssessmentRegistryProtectionInfoTypeEnum'
)
AssessmentRegistryProtectionRiskTypeEnum = convert_enum_to_graphene_enum(
    AssessmentRegistry.ProtectionRiskType, name='AssessmentRegistryProtectionRiskTypeEnum'
)
AssessmentRegistryStatusTypeEnum = convert_enum_to_graphene_enum(
    AssessmentRegistry.StatusType, name='AssessmentRegistryStatusTypeEnum'
)
AssessmentRegistryAffectedGroupTypeEnum = convert_enum_to_graphene_enum(
    AssessmentRegistry.AffectedGroupType, name='AssessmentRegistryAffectedGroupTypeEnum'
)
AssessmentRegistryDataCollectionTechniqueTypeEnum = convert_enum_to_graphene_enum(
    MethodologyAttribute.CollectionTechniqueType, name='AssessmentRegistryDataCollectionTechniqueTypeEnum'
)
AssessmentRegistrySamplingApproachTypeEnum = convert_enum_to_graphene_enum(
    MethodologyAttribute.SamplingApproachType, name='AssessmentRegistrySamplingApproachTypeEnum'
)
AssessmentRegistryProximityTypeEnum = convert_enum_to_graphene_enum(
    MethodologyAttribute.ProximityType, name='AssessmentRegistryProximityTypeEnum'
)
AssessmentRegistryUnitOfAnalysisTypeEnum = convert_enum_to_graphene_enum(
    MethodologyAttribute.UnitOfAnalysisType, name='AssessmentRegistryUnitOfAnalysisTypeEnum'
)
AssessmentRegistryUnitOfReportingTypeEnum = convert_enum_to_graphene_enum(
    MethodologyAttribute.UnitOfReportingType, name='AssessmentRegistryUnitOfReportingTypeEnum'
)
AssessmentRegistryDocumentTypeEnum = convert_enum_to_graphene_enum(
    AdditionalDocument.DocumentType, name='AssessmentRegistryDocumentTypeEnum'
)
AssessmentRegistryScoreCriteriaTypeEnum = convert_enum_to_graphene_enum(
    ScoreRating.ScoreCriteria, name='AssessmentRegistryScoreCriteriaTypeEnum'
)
AssessmentRegistryScoreAnalyticalStatementTypeEnum = convert_enum_to_graphene_enum(
    ScoreRating.AnalyticalStatement, name='AssessmentRegistryScoreAnalyticalStatementTypeEnum'
)
AssessmentRegistryAnalysisLevelTypeEnum = convert_enum_to_graphene_enum(
    ScoreAnalyticalDensity.AnalysisLevelCovered, name='AssessmentRegistryAnalysisLevelTypeEnum'
)
AssessmentRegistryAnalysisFigureTypeEnum = convert_enum_to_graphene_enum(
    ScoreAnalyticalDensity.FigureProvidedByAssessment, name='AssessmentRegistryAnalysisFigureTypeEnum'
)
AssessmentRegistryRatingTypeEnum = convert_enum_to_graphene_enum(
    ScoreRating.RatingType, name='AssessmentRegistryRatingType'
)
AssessmentRegistryCNAQuestionSectorTypeEnum = convert_enum_to_graphene_enum(
    Question.QuestionSector, name='AssessmentRegistryCNAQuestionSectorTypeEnum'
)
AssessmentRegistryCNAQuestionSubSectorTypeEnum = convert_enum_to_graphene_enum(
    Question.QuestionSubSector, name='AssessmentRegistryCNAQuestionSubSectorTypeEnum'
)
AssessmentRegistrySummaryPillarTypeEnum = convert_enum_to_graphene_enum(
    Summary.Pillar, name='AssessmentRegistrySummaryPillarTypeEnum'
)
AssessmentRegistrySummaryFocusDimensionTypeEnum = convert_enum_to_graphene_enum(
    SummaryFocus.Dimension, name='AssessmentRegistrySummaryFocusDimensionTypeEnum'
)
AssessmentRegistrySummarySubDimensionTypeEnum = convert_enum_to_graphene_enum(
    SummaryIssue.SubDimension, name='AssessmentRegistrySummarySubDimensionTypeEnum'
)
AssessmentRegistrySummarySubPillarTypeEnum = convert_enum_to_graphene_enum(
    SummaryIssue.SubPillar, name='AssessmentRegistrySummarySubPillarTypeEnum'
)
AssessmentRegistryOrganizationTypeEnum = convert_enum_to_graphene_enum(
    AssessmentRegistryOrganization.Type, name='AssessmentRegistryOrganizationTypeEnum'
)
enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (AssessmentRegistry.bg_crisis_type, AssessmentRegistryCrisisTypeEnum),
        (AssessmentRegistry.bg_preparedness, AssessmentRegistryPreparednessTypeEnum),
        (AssessmentRegistry.external_support, AssessmentRegistryExternalSupportTypeEnum),
        (AssessmentRegistry.coordinated_joint, AssessmentRegistryCoordinationTypeEnum),
        (AssessmentRegistry.details_type, AssessmentRegistryDetailTypeEnum),
        (AssessmentRegistry.family, AssessmentRegistryFamilyTypeEnum),
        (AssessmentRegistry.status, AssessmentRegistryStatusTypeEnum),
        (AssessmentRegistry.frequency, AssessmentRegistryFrequencyTypeEnum),
        (AssessmentRegistry.confidentiality, AssessmentRegistryConfidentialityTypeEnum),
        (AssessmentRegistry.language, AssessmentRegistryLanguageTypeEnum),
        (AssessmentRegistry.focuses, AssessmentRegistryFocusTypeEnum),
        (AssessmentRegistry.sectors, AssessmentRegistrySectorTypeEnum),
        (AssessmentRegistry.protection_info_mgmts, AssessmentRegistryProtectionInfoTypeEnum),
        (AssessmentRegistry.protection_risks, AssessmentRegistryProtectionRiskTypeEnum),
        (AssessmentRegistry.affected_groups, AssessmentRegistryAffectedGroupTypeEnum),
        (MethodologyAttribute.data_collection_technique, AssessmentRegistryDataCollectionTechniqueTypeEnum),
        (MethodologyAttribute.sampling_approach, AssessmentRegistrySamplingApproachTypeEnum),
        (MethodologyAttribute.proximity, AssessmentRegistryProximityTypeEnum),
        (MethodologyAttribute.unit_of_analysis, AssessmentRegistryUnitOfAnalysisTypeEnum),
        (MethodologyAttribute.unit_of_reporting, AssessmentRegistryUnitOfReportingTypeEnum),
        (AdditionalDocument.document_type, AssessmentRegistryDocumentTypeEnum),
        (ScoreRating.score_type, AssessmentRegistryScoreCriteriaTypeEnum),
        (ScoreRating.rating, AssessmentRegistryRatingTypeEnum),
        (ScoreAnalyticalDensity.sector, AssessmentRegistrySectorTypeEnum),
        (ScoreAnalyticalDensity.analysis_level_covered, AssessmentRegistryAnalysisLevelTypeEnum),
        (ScoreAnalyticalDensity.figure_provided, AssessmentRegistryAnalysisFigureTypeEnum),
        (SummarySubDimensionIssue.sector, AssessmentRegistrySectorTypeEnum),
        (SummaryIssue.sub_pillar, AssessmentRegistrySummarySubPillarTypeEnum),
        (SummaryIssue.sub_dimension, AssessmentRegistrySummarySubDimensionTypeEnum),
        (SummaryFocus.sector, AssessmentRegistrySectorTypeEnum),
        (AssessmentRegistryOrganization.organization_type, AssessmentRegistryOrganizationTypeEnum),
    )
}
