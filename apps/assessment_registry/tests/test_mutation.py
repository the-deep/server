from utils.graphene.tests import GraphQLTestCase, GraphQLSnapShotTestCase

from organization.factories import OrganizationFactory
from geo.factories import GeoAreaFactory, AdminLevelFactory, RegionFactory
from gallery.factories import FileFactory
from project.factories import ProjectFactory
from project.models import ProjectOrganization
from user.factories import UserFactory
from lead.factories import LeadFactory
from assessment_registry.factories import (
    AssessmentRegistryFactory,
    AssessmentRegistryOrganizationFactory,
    QuestionFactory,
    SummaryIssueFactory,
)
from assessment_registry.models import (
    AssessmentRegistry,
    AssessmentRegistryOrganization,
    MethodologyAttribute,
    AdditionalDocument,
    ScoreRating,
    Question,
    ScoreAnalyticalDensity,
)


class TestAssessmentRegistryMutation(GraphQLTestCase):
    CREATE_ASSESSMENT_REGISTRY_QUERY = '''
        mutation MyMutation ($projectId: ID!, $input: AssessmentRegistryCreateInputType!) {
            project(id:$projectId) {
                 createAssessmentRegistry(data: $input) {
                 ok
                 errors
                 result {
                    id
                    affectedGroups
                    bgCrisisStartDate
                    confidentiality
                    confidentialityDisplay
                    coordinatedJoint
                    coordinatedJointDisplay
                    costEstimatesUsd
                    createdAt
                    dataCollectionEndDate
                    dataCollectionStartDate
                    dataCollectionTechniques
                    detailsType
                    detailsTypeDisplay
                    externalSupport
                    externalSupportDisplay
                    family
                    familyDisplay
                    metadataComplete
                    focuses
                    frequency
                    frequencyDisplay
                    language
                    limitations
                    modifiedAt
                    noOfPages
                    objectives
                    protectionInfoMgmts
                    protectionRisks
                    publicationDate
                    sampling
                    sectors
                    focusComplete
                    lead {
                      id
                    }
                    methodologyAttributes {
                      unitOfReportingDisplay
                      unitOfReporting
                      unitOfAnalysis
                      unitOfAnalysisDisplay
                      samplingApproach
                      samplingAppraochDisplay
                      proximity
                      proximityDisplay
                      id
                      dataCollectionTechniqueDisplay
                      dataCollectionTechnique
                    }
                    methodologyComplete
                    additionalDocuments {
                        documentType
                        documentTypeDisplay
                        externalLink
                        id
                        file {
                            id
                            mimeType
                            metadata
                        }
                    }
                    additionalDocumentComplete
                   cna {
                      answer
                      id
                      question {
                        id
                        question
                        sector
                        subSector
                        sectorDisplay
                        subSectorDisplay
                      }
                   }
                   cnaComplete
                   summaryDimensionMeta {
                      id
                      percentageInNeed
                   }
                   summarySubDimensionIssue {
                      id
                   }
                   summaryPillarMeta {
                      id
                      totalPeopleAssessed
                   }
                   summarySubPillarIssue {
                      id
                   }
                   summaryComplete
                }
            }
        }
    }
'''

    def setUp(self):
        super().setUp()
        self.member_user = UserFactory.create()
        self.project1 = ProjectFactory.create()
        self.lead1 = LeadFactory.create(project=self.project1)
        self.organization1 = OrganizationFactory.create()
        self.organization2 = OrganizationFactory.create()
        self.region = RegionFactory.create()
        self.admin_level1 = AdminLevelFactory.create(region=self.region)
        self.geo_area1 = GeoAreaFactory.create(admin_level=self.admin_level1)
        self.geo_area2 = GeoAreaFactory.create(admin_level=self.admin_level1)
        self.question1 = QuestionFactory.create(
            sector=Question.QuestionSector.RELEVANCE.value,
            sub_sector=Question.QuestionSubSector.RELEVANCE.value,
            question="test question"
        )
        self.file = FileFactory.create()
        self.project1.add_member(self.member_user, role=self.project_role_member)
        self.summary_issue1, self.summary_issue2, self.summary_issue3 = SummaryIssueFactory.create_batch(3)

    def test_create_assessment_registry(self):
        def _query_check(minput, **kwargs):
            return self.query_check(
                self.CREATE_ASSESSMENT_REGISTRY_QUERY,
                minput=minput,
                variables={'projectId': self.project1.id},
                **kwargs
            )

        minput = dict(
            bgCrisisStartDate="2023-01-01",
            bgCrisisType=self.genum(AssessmentRegistry.CrisisType.EARTH_QUAKE),
            bgPreparedness=self.genum(AssessmentRegistry.PreparednessType.WITH_PREPAREDNESS),
            confidentiality=self.genum(AssessmentRegistry.ConfidentialityType.UNPROTECTED),
            coordinatedJoint=self.genum(AssessmentRegistry.CoordinationType.COORDINATED),
            costEstimatesUsd=10,
            status=self.genum(AssessmentRegistry.StatusType.PLANNED),
            detailsType=self.genum(AssessmentRegistry.Type.INITIAL),
            externalSupport=self.genum(AssessmentRegistry.ExternalSupportType.EXTERNAL_SUPPORT_RECIEVED),
            family=self.genum(AssessmentRegistry.FamilyType.DISPLACEMENT_TRAKING_MATRIX),
            focuses=[
                self.genum(AssessmentRegistry.FocusType.CONTEXT),
                self.genum(AssessmentRegistry.FocusType.HUMANITERIAN_ACCESS),
                self.genum(AssessmentRegistry.FocusType.DISPLACEMENT)
            ],
            frequency=self.genum(AssessmentRegistry.FrequencyType.ONE_OFF),
            protectionInfoMgmts=[
                self.genum(AssessmentRegistry.ProtectionInfoType.PROTECTION_MONITORING),
                self.genum(AssessmentRegistry.ProtectionInfoType.PROTECTION_NEEDS_ASSESSMENT)
            ],
            protectionRisks=[
                self.genum(AssessmentRegistry.ProtectionRiskType.ABDUCATION_KIDNAPPING),
                self.genum(AssessmentRegistry.ProtectionRiskType.ATTACKS_ON_CIVILIANS)
            ],
            sectors=[
                self.genum(AssessmentRegistry.SectorType.HEALTH),
                self.genum(AssessmentRegistry.SectorType.SHELTER),
                self.genum(AssessmentRegistry.SectorType.WASH)
            ],
            lead=self.lead1.id,
            locations=[self.geo_area1.id, self.geo_area2.id],
            dataCollectionEndDate="2023-01-01",
            dataCollectionStartDate="2023-01-01",
            dataCollectionTechniques="Test Data",
            limitations="test",
            objectives="test",
            noOfPages=10,
            publicationDate="2023-01-01",
            sampling="test",
            language=[
                self.genum(AssessmentRegistry.Language.ENGLISH),
                self.genum(AssessmentRegistry.Language.SPANISH)
            ],
            bgCountries=[self.region.id],
            affectedGroups=[self.genum(AssessmentRegistry.AffectedGroupType.ALL_AFFECTED)],
            metadataComplete=True,
            additionalDocumentComplete=True,
            focusComplete=True,
            methodologyComplete=True,
            methodologyAttributes=[
                dict(
                    dataCollectionTechnique=self.genum(MethodologyAttribute.CollectionTechniqueType.SECONDARY_DATA_REVIEW),
                    proximity=self.genum(MethodologyAttribute.ProximityType.FACE_TO_FACE),
                    samplingApproach=self.genum(MethodologyAttribute.SamplingApproachType.NON_RANDOM_SELECTION),
                    samplingSize=10,
                    unitOfAnalysis=self.genum(MethodologyAttribute.UnitOfAnalysisType.CRISIS),
                    unitOfReporting=self.genum(MethodologyAttribute.UnitOfReportingType.CRISIS)
                ),
            ],
            additionalDocuments=[
                dict(
                    documentType=self.genum(AdditionalDocument.DocumentType.ASSESSMENT_DATABASE),
                    externalLink="",
                    file=str(self.file.id)
                ),
            ],
            scoreRatings=[
                dict(
                    scoreType=self.genum(ScoreRating.ScoreCriteria.ASSUMPTIONS),
                    rating=self.genum(ScoreRating.RatingType.VERY_POOR),
                    reason="test"
                ),
                dict(
                    scoreType=self.genum(ScoreRating.ScoreCriteria.RELEVANCE),
                    rating=self.genum(ScoreRating.RatingType.VERY_POOR),
                    reason="test"
                )
            ],
            scoreAnalyticalDensity=[
                dict(
                    sector=self.genum(AssessmentRegistry.SectorType.FOOD_SECURITY),
                    analysisLevelCovered=[
                        self.genum(ScoreAnalyticalDensity.AnalysisLevelCovered.ISSUE_UNMET_NEEDS_ARE_DETAILED),
                        self.genum(ScoreAnalyticalDensity.AnalysisLevelCovered.ISSUE_UNMET_NEEDS_ARE_PRIORITIZED_RANKED),
                    ],
                    figureProvided=[
                        self.genum(ScoreAnalyticalDensity.FigureProvidedByAssessment.TOTAL_POP_IN_THE_ASSESSED_AREAS),
                    ],
                    score=1,
                ),
                dict(
                    sector=self.genum(AssessmentRegistry.SectorType.SHELTER),
                    analysisLevelCovered=[],
                    score=2
                )
            ],
            cna=[
                dict(
                    answer=True,
                    question=self.question1.id,
                )
            ],
            summaryPillarMeta=dict(
                totalPeopleAssessed=1000
            ),
            summarySubPillarIssue=[
                dict(
                    summaryIssue=self.summary_issue1.id,
                    order=1,
                )
            ],
            summaryDimensionMeta=[
                dict(
                    percentageInNeed=10,
                    sector=self.genum(AssessmentRegistry.SectorType.FOOD_SECURITY),
                ),
                dict(
                    percentageInNeed=10,
                    sector=self.genum(AssessmentRegistry.SectorType.SHELTER),
                ),
            ],
            summarySubDimensionIssue=[
                dict(
                    summaryIssue=self.summary_issue2.id,
                    sector=self.genum(AssessmentRegistry.SectorType.FOOD_SECURITY),
                    order=1,
                )
            ]
        )
        self.force_login(self.member_user)
        content = _query_check(minput, okay=False)
        data = content['data']['project']['createAssessmentRegistry']['result']
        self.assertEqual(data['costEstimatesUsd'], minput['costEstimatesUsd'], data)
        self.assertIsNotNone(data['methodologyAttributes'])
        self.assertIsNotNone(data['additionalDocuments'])
        self.assertIsNotNone(data['cna'])
        self.assertIsNotNone(data['summaryPillarMeta'])
        self.assertIsNotNone(data['summaryDimensionMeta'])
        self.assertIsNotNone(data['summarySubPillarIssue'])
        self.assertIsNotNone(data['summarySubDimensionIssue'])
        self.assertEqual(data['metadataComplete'], True)
        self.assertIsNotNone(data['protectionRisks'])


class TestAssessmentRegistryMutationSnapShotTestCase(GraphQLSnapShotTestCase):
    UPDATE_ASSESSMENT_REGISTRY_QUERY = '''
            mutation MyMutation(
                $projectId: ID!,
                $input: AssessmentRegistryCreateInputType!,
                $assessmentRegistryId: ID!
            ) {
              project(id: $projectId) {
                updateAssessmentRegistry(data: $input, id: $assessmentRegistryId) {
                  ok
                  errors
                  result {
                    id
                    affectedGroups
                    bgPreparedness
                    bgCountries {
                      id
                    }
                    bgCrisisStartDate
                    bgCrisisType
                    confidentiality
                    confidentialityDisplay
                    coordinatedJoint
                    coordinatedJointDisplay
                    costEstimatesUsd
                    createdAt
                    dataCollectionEndDate
                    dataCollectionStartDate
                    dataCollectionTechniques
                    detailsType
                    detailsTypeDisplay
                    externalSupport
                    externalSupportDisplay
                    family
                    familyDisplay
                    metadataComplete
                    focuses
                    frequency
                    frequencyDisplay
                    language
                    limitations
                    modifiedAt
                    noOfPages
                    objectives
                    protectionInfoMgmts
                    protectionRisks
                    publicationDate
                    sampling
                    sectors
                    status
                    focusComplete
                    lead {
                      id
                    }
                    methodologyAttributes {
                      unitOfReportingDisplay
                      unitOfReporting
                      unitOfAnalysis
                      unitOfAnalysisDisplay
                      samplingApproach
                      samplingAppraochDisplay
                      proximity
                      proximityDisplay
                      id
                      dataCollectionTechniqueDisplay
                      dataCollectionTechnique
                    }
                    methodologyComplete
                    additionalDocuments {
                      documentType
                      documentTypeDisplay
                      externalLink
                      id
                      file {
                        id
                        mimeType
                        metadata
                      }
                    }
                    additionalDocumentComplete
                    cna {
                      answer
                      id
                      question {
                        id
                        question
                        sector
                        subSector
                        sectorDisplay
                        subSectorDisplay
                      }
                    }
                    cnaComplete
                    summaryDimensionMeta {
                      id
                      percentageInNeed
                    }
                    summarySubDimensionIssue {
                      id
                    }
                    summaryPillarMeta {
                      id
                      totalPeopleAssessed
                    }
                    summarySubPillarIssue {
                      id
                    }
                    summaryComplete
                  }
                }
              }
            }
    '''

    def setUp(self):
        super().setUp()
        # Users with different roles
        self.non_member_user, self.readonly_member_user, self.member_user = UserFactory.create_batch(3)
        self.project = ProjectFactory.create()
        # leads
        self.lead1, self.lead2 = LeadFactory.create_batch(2, project=self.project)
        self.lead3 = LeadFactory.create()
        # organizations
        self.organization1, self.organization2 = OrganizationFactory.create_batch(2)
        # region
        self.region = RegionFactory.create()
        self.question = QuestionFactory.create(
            sector=Question.QuestionSector.RELEVANCE.value,
            sub_sector=Question.QuestionSubSector.RELEVANCE.value,
            question="test question"
        )
        self.project.add_member(self.readonly_member_user, role=self.project_role_reader)
        self.project.add_member(self.member_user, role=self.project_role_member)
        self.assessment_registry = AssessmentRegistryFactory.create(
            project=self.project,
            lead=self.lead1,
            bg_crisis_type=AssessmentRegistry.CrisisType.EARTH_QUAKE,
            bg_preparedness=AssessmentRegistry.PreparednessType.WITH_PREPAREDNESS,
            confidentiality=AssessmentRegistry.ConfidentialityType.UNPROTECTED,
            coordinated_joint=AssessmentRegistry.CoordinationType.COORDINATED,
            status=AssessmentRegistry.StatusType.PLANNED,
            details_type=AssessmentRegistry.Type.INITIAL,
            external_support=AssessmentRegistry.ExternalSupportType.EXTERNAL_SUPPORT_RECIEVED,
            family=AssessmentRegistry.FamilyType.DISPLACEMENT_TRAKING_MATRIX,
            frequency=AssessmentRegistry.FrequencyType.ONE_OFF,
            language=[
                AssessmentRegistry.Language.ENGLISH,
                AssessmentRegistry.Language.SPANISH,
            ],
            bg_countries=[self.region.id],
            metadata_complete=True,
            additional_document_complete=True,
            focus_complete=True,
            methodology_complete=True,
            summary_complete=True,
            cna_complete=True,
            score_complete=True,
            bg_crisis_start_date='2019-07-03',
            data_collection_start_date='2020-02-16',
            data_collection_end_date='2020-09-06',
            publication_date='2021-06-21',
            focuses=[
                AssessmentRegistry.FocusType.CONTEXT,
                AssessmentRegistry.FocusType.HUMANITERIAN_ACCESS,
                AssessmentRegistry.FocusType.DISPLACEMENT
            ],
            sectors=[
                AssessmentRegistry.SectorType.HEALTH,
                AssessmentRegistry.SectorType.SHELTER,
                AssessmentRegistry.SectorType.WASH,
            ],
            protection_info_mgmts=[AssessmentRegistry.ProtectionInfoType.PROTECTION_MONITORING],
            affected_groups=[AssessmentRegistry.AffectedGroupType.ALL_AFFECTED],
        )
        self.stakeholders = AssessmentRegistryOrganizationFactory.create(
            organization_type=AssessmentRegistryOrganization.Type.LEAD_ORGANIZATION,
            organization=self.organization1,
            assessment_registry=self.assessment_registry
        )
        self.minput = dict(
            bgCrisisType=self.genum(AssessmentRegistry.CrisisType.LANDSLIDE),
            bgPreparedness=self.genum(AssessmentRegistry.PreparednessType.WITHOUT_PREPAREDNESS),
            confidentiality=self.genum(AssessmentRegistry.ConfidentialityType.CONFIDENTIAL),
            coordinatedJoint=self.genum(AssessmentRegistry.CoordinationType.HARMONIZED),
            status=self.genum(AssessmentRegistry.StatusType.ONGOING),
            detailsType=self.genum(AssessmentRegistry.Type.MONITORING),
            externalSupport=self.genum(AssessmentRegistry.ExternalSupportType.NO_EXTERNAL_SUPPORT_RECEIVED),
            family=self.genum(AssessmentRegistry.FamilyType.HUMANITARIAN_NEEDS_OVERVIEW),
            frequency=self.genum(AssessmentRegistry.FrequencyType.REGULAR),
            lead=self.lead2.id,
            language=[
                self.genum(AssessmentRegistry.Language.ENGLISH),
                self.genum(AssessmentRegistry.Language.FRENCH)
            ],
            bgCountries=[self.region.id],
            scoreRatings=[
                dict(
                    scoreType=self.genum(ScoreRating.ScoreCriteria.ASSUMPTIONS),
                    rating=self.genum(ScoreRating.RatingType.VERY_POOR),
                    reason="test"
                ),
                dict(
                    scoreType=self.genum(ScoreRating.ScoreCriteria.RELEVANCE),
                    rating=self.genum(ScoreRating.RatingType.VERY_POOR),
                    reason="test"
                )
            ],
            scoreAnalyticalDensity=[
                dict(
                    sector=self.genum(AssessmentRegistry.SectorType.FOOD_SECURITY),
                    analysisLevelCovered=[
                        self.genum(ScoreAnalyticalDensity.AnalysisLevelCovered.ISSUE_UNMET_NEEDS_ARE_DETAILED),
                        self.genum(ScoreAnalyticalDensity.AnalysisLevelCovered.ISSUE_UNMET_NEEDS_ARE_PRIORITIZED_RANKED),
                    ],
                    figureProvided=[
                        self.genum(ScoreAnalyticalDensity.FigureProvidedByAssessment.TOTAL_POP_IN_THE_ASSESSED_AREAS),
                    ],
                    score=1,
                ),
                dict(
                    sector=self.genum(AssessmentRegistry.SectorType.SHELTER),
                    analysisLevelCovered=[],
                    score=2
                )
            ],
            stakeholders=[
                dict(
                    organization=self.stakeholders.id,
                    organizationType=self.genum(ProjectOrganization.Type.LEAD_ORGANIZATION),
                ),
                dict(
                    organization=self.stakeholders.id,
                    organizationType=self.genum(ProjectOrganization.Type.INTERNATIONAL_PARTNER),
                ),
            ],
            cna=[
                dict(
                    answer=True,
                    question=self.question.id,
                )
            ],
        )

    def test_assessment_registry_update(self):
        """
        This test makes sure only valid users can update AssessmentRegistry
        """
        def _query_check(minput, **kwargs):
            return self.query_check(
                self.UPDATE_ASSESSMENT_REGISTRY_QUERY,
                minput=minput,
                variables={'projectId': self.project.id, 'assessmentRegistryId': self.assessment_registry.id},
                **kwargs
            )

        # -- Without login
        _query_check(self.minput, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(self.minput, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(self.minput, assert_for_error=True)

        # --- member user
        self.force_login(self.member_user)

        # Valid input
        response = _query_check(self.minput)
        self.assertMatchSnapshot(response, 'success')

        # Invalid inputs
        self.minput['scoreRatings'] = [
            dict(
                scoreType=self.genum(ScoreRating.ScoreCriteria.ASSUMPTIONS),
                rating=self.genum(ScoreRating.RatingType.VERY_POOR),
                reason="test"
            ),
            dict(
                scoreType=self.genum(ScoreRating.ScoreCriteria.ASSUMPTIONS),
                rating=self.genum(ScoreRating.RatingType.VERY_POOR),
                reason="test"
            )
        ]
        self.minput['scoreAnalyticalDensity'] = [
            dict(
                sector=self.genum(AssessmentRegistry.SectorType.FOOD_SECURITY),
                analysisLevelCovered=[
                    self.genum(ScoreAnalyticalDensity.AnalysisLevelCovered.ISSUE_UNMET_NEEDS_ARE_DETAILED),
                    self.genum(ScoreAnalyticalDensity.AnalysisLevelCovered.ISSUE_UNMET_NEEDS_ARE_PRIORITIZED_RANKED),
                ],
                figureProvided=[
                    self.genum(ScoreAnalyticalDensity.FigureProvidedByAssessment.TOTAL_POP_IN_THE_ASSESSED_AREAS),
                ],
                score=1,
            ),
            dict(
                sector=self.genum(AssessmentRegistry.SectorType.FOOD_SECURITY),
                analysisLevelCovered=[],
                score=1,
            )
        ]
        self.minput['stakeholders'] = [
            dict(
                organization=self.stakeholders.id,
                organizationType=self.genum(ProjectOrganization.Type.LEAD_ORGANIZATION),
            ),
            dict(
                organization=self.stakeholders.id,
                organizationType=self.genum(ProjectOrganization.Type.LEAD_ORGANIZATION),
            ),
        ]
        self.minput['cna'] = [
            dict(
                answer=True,
                question=self.question.id,
            ),
            dict(
                answer=True,
                question=self.question.id,
            ),
        ]
        self.minput['lead'] = self.lead3.id

        response = _query_check(self.minput, okay=False)
        self.assertMatchSnapshot(response, "error")
