from assessment_registry.factories import QuestionFactory, SummaryIssueFactory
from assessment_registry.models import (
    AdditionalDocument,
    AssessmentRegistry,
    MethodologyAttribute,
    Question,
    ScoreAnalyticalDensity,
    ScoreRating,
)
from gallery.factories import FileFactory
from geo.factories import AdminLevelFactory, GeoAreaFactory, RegionFactory
from lead.factories import LeadFactory
from organization.factories import OrganizationFactory
from project.factories import ProjectFactory
from user.factories import UserFactory

from utils.graphene.tests import GraphQLTestCase


class TestAssessmentRegistryMutation(GraphQLTestCase):
    CREATE_ASSESSMENT_REGISTRY_QUERY = """
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
"""

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
            question="test question",
        )
        self.file = FileFactory.create()
        self.project1.add_member(self.member_user, role=self.project_role_member)
        self.summary_issue1, self.summary_issue2, self.summary_issue3 = SummaryIssueFactory.create_batch(3)

    def test_create_assessment_registry(self):
        def _query_check(minput, **kwargs):
            return self.query_check(
                self.CREATE_ASSESSMENT_REGISTRY_QUERY, minput=minput, variables={"projectId": self.project1.id}, **kwargs
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
                self.genum(AssessmentRegistry.FocusType.DISPLACEMENT),
            ],
            frequency=self.genum(AssessmentRegistry.FrequencyType.ONE_OFF),
            protectionInfoMgmts=[
                self.genum(AssessmentRegistry.ProtectionInfoType.PROTECTION_MONITORING),
                self.genum(AssessmentRegistry.ProtectionInfoType.PROTECTION_NEEDS_ASSESSMENT),
            ],
            protectionRisks=[
                self.genum(AssessmentRegistry.ProtectionRiskType.ABDUCATION_KIDNAPPING),
                self.genum(AssessmentRegistry.ProtectionRiskType.ATTACKS_ON_CIVILIANS),
            ],
            sectors=[
                self.genum(AssessmentRegistry.SectorType.HEALTH),
                self.genum(AssessmentRegistry.SectorType.SHELTER),
                self.genum(AssessmentRegistry.SectorType.WASH),
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
            language=[self.genum(AssessmentRegistry.Language.ENGLISH), self.genum(AssessmentRegistry.Language.SPANISH)],
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
                    unitOfReporting=self.genum(MethodologyAttribute.UnitOfReportingType.CRISIS),
                ),
            ],
            additionalDocuments=[
                dict(
                    documentType=self.genum(AdditionalDocument.DocumentType.ASSESSMENT_DATABASE),
                    externalLink="",
                    file=str(self.file.id),
                ),
            ],
            scoreRatings=[
                dict(
                    scoreType=self.genum(ScoreRating.ScoreCriteria.ASSUMPTIONS),
                    rating=self.genum(ScoreRating.RatingType.VERY_POOR),
                    reason="test",
                ),
                dict(
                    scoreType=self.genum(ScoreRating.ScoreCriteria.RELEVANCE),
                    rating=self.genum(ScoreRating.RatingType.VERY_POOR),
                    reason="test",
                ),
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
                dict(sector=self.genum(AssessmentRegistry.SectorType.SHELTER), analysisLevelCovered=[], score=2),
            ],
            cna=[
                dict(
                    answer=True,
                    question=self.question1.id,
                )
            ],
            summaryPillarMeta=dict(totalPeopleAssessed=1000),
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
            ],
        )
        self.force_login(self.member_user)
        content = _query_check(minput, okay=False)
        data = content["data"]["project"]["createAssessmentRegistry"]["result"]
        self.assertEqual(data["costEstimatesUsd"], minput["costEstimatesUsd"], data)
        self.assertIsNotNone(data["methodologyAttributes"])
        self.assertIsNotNone(data["additionalDocuments"])
        self.assertIsNotNone(data["cna"])
        self.assertIsNotNone(data["summaryPillarMeta"])
        self.assertIsNotNone(data["summaryDimensionMeta"])
        self.assertIsNotNone(data["summarySubPillarIssue"])
        self.assertIsNotNone(data["summarySubDimensionIssue"])
        self.assertEqual(data["metadataComplete"], True)
        self.assertIsNotNone(data["protectionRisks"])
