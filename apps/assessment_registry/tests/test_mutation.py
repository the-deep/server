from utils.graphene.tests import GraphQLTestCase

from organization.factories import OrganizationFactory
from geo.factories import RegionFactory
from gallery.factories import FileFactory
from project.factories import ProjectFactory
from user.factories import UserFactory
from lead.factories import LeadFactory
from assessment_registry.factories import (
    QuestionFactory,
    SummaryIssueFactory,
)
from assessment_registry.models import (
    AssessmentRegistry,
    MethodologyAttribute,
    AdditionalDocument,
    ScoreRating,
    Question,
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
                    affectedGroupsDisplay
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
                    focuses
                    frequency
                    frequencyDisplay
                    language
                    limitations
                    modifiedAt
                    noOfPages
                    objectives
                    protectionInfoMgmts
                    publicationDate
                    sampling
                    sectors
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
                   summaryFocusMeta {
                      id
                      percentageInNeed
                   }
                   summaryFocusSubsectorIssue {
                      id
                   }
                   summaryMeta {
                      id
                      totalPeopleAssessed
                   }
                   summarySubsectorIssue {
                      id
                   }
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
        self.region1 = RegionFactory.create()
        self.region2 = RegionFactory.create()
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
            sectors=[
                self.genum(AssessmentRegistry.SectorType.HEALTH),
                self.genum(AssessmentRegistry.SectorType.SHELTER),
                self.genum(AssessmentRegistry.SectorType.WASH)
            ],
            governments=[self.organization1.id, self.organization2.id],
            internationalPartners=[self.organization1.id, self.organization2.id],
            lead=self.lead1.id,
            leadOrganizations=[self.organization1.id, self.organization2.id],
            locations=[self.region1.id, self.region2.id],
            nationalPartners=[self.organization1.id, self.organization2.id],
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
            bgCountries=[self.region1.id, self.region2.id],
            donors=[self.organization1.id, self.organization2.id],
            affectedGroups=self.genum(AssessmentRegistry.AffectedGroupType.ALL_AFFECTED),
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
                    documentType=self.genum(AdditionalDocument.DocumentType.EXECUTIVE_SUMMARY),
                    externalLink="",
                    file=str(self.file.id)
                ),
            ],
            scoreAnalyticalDensity=[
                dict(
                    sector=self.genum(AssessmentRegistry.SectorType.FOOD_SECURITY),
                    value=10
                ),
                dict(
                    sector=self.genum(AssessmentRegistry.SectorType.SHELTER),
                    value=10
                )
            ],
            scoreRatings=[
                dict(
                    scoreType=self.genum(ScoreRating.ScoreType.ASSUMPTIONS),
                    rating=self.genum(ScoreRating.RatingType.VERY_POOR),
                    reason="test"
                ),
                dict(
                    scoreType=self.genum(ScoreRating.ScoreType.RELEVANCE),
                    rating=self.genum(ScoreRating.RatingType.VERY_POOR),
                    reason="test"
                )
            ],
            cna=[
                dict(
                    answer=True,
                    question=self.question1.id,
                )
            ],
            summaryMeta=[
                dict(
                    totalPeopleAssessed=1000
                )
            ],
            summarySubsectorIssue=[
                dict(
                    summaryIssue=self.summary_issue1.id
                )
            ],
            summaryFocusMeta=[
                dict(
                    percentageInNeed=10
                )
            ],
            summaryFocusIssue=[
                dict(
                    summaryIssue=self.summary_issue2.id,
                    focus=self.genum(AssessmentRegistry.FocusType.CONTEXT),
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
        self.assertIsNotNone(data['summaryMeta'])
        self.assertIsNotNone(data['summaryFocusMeta'])
        self.assertIsNotNone(data['summarySubsectorIssue'])
        self.assertIsNotNone(data['summaryFocusSubsectorIssue'])
