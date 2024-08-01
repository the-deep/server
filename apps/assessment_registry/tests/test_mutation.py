from utils.graphene.tests import GraphQLTestCase, GraphQLSnapShotTestCase

from organization.factories import OrganizationFactory
from geo.factories import GeoAreaFactory, AdminLevelFactory, RegionFactory
from gallery.factories import FileFactory
from project.factories import ProjectFactory
from user.factories import UserFactory
from lead.factories import LeadFactory
from assessment_registry.factories import (
    AssessmentRegistryFactory,
    QuestionFactory,
    SummaryIssueFactory,
)
from assessment_registry.models import (
    AssessmentRegistry,
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
    UPDATE_ASSESSMENT_REGISTRY_QUERY = '''
        mutation MyMutation ($projectId: ID!, $input: AssessmentRegistryCreateInputType!, $assessmentRegistryId: ID!) {
          project(id: $projectId) {
            updateAssessmentRegistry(data: $input, id: $assessmentRegistryId) {
              ok
              errors
              result {
                id
                bgPreparedness
                bgCountries {
                  id
                }
                bgCrisisType
                confidentiality
                coordinatedJoint
                detailsType
                externalSupport
                family
                frequency
                language
                status
                lead {
                  id
                }
              }
            }
          }
        }
'''

    def setUp(self):
        super().setUp()
        # Users with different roles
        self.non_member_user = UserFactory.create()
        self.readonly_member_user = UserFactory.create()
        self.member_user = UserFactory.create()
        self.project1 = ProjectFactory.create()
        self.lead1, self.lead2, self.lead3 = LeadFactory.create_batch(3, project=self.project1)
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
        self.project1.add_member(self.readonly_member_user, role=self.project_role_reader)
        self.project1.add_member(self.member_user, role=self.project_role_member)
        self.summary_issue1, self.summary_issue2, self.summary_issue3 = SummaryIssueFactory.create_batch(3)
        self.assessment_registry = AssessmentRegistryFactory.create(
            project=self.project1,
            lead=self.lead3,
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
        )

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

    def test_update_assessment_registry(self):
        def _query_check(mutation, minput, variables, assert_for_error=False, **kwargs):
            return self.query_check(
                mutation,
                minput=minput,
                variables=variables,
                assert_for_error=assert_for_error,
                **kwargs
            )

        update_minput = dict(
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
        )
        # -- Without login
        _query_check(
            self.UPDATE_ASSESSMENT_REGISTRY_QUERY,
            update_minput,
            variables={'projectId': self.project1.id, 'assessmentRegistryId': self.assessment_registry.id},
            assert_for_error=True,
            okay=False
        )

        user_roles = [self.non_member_user, self.readonly_member_user]
        for user in user_roles:
            self.force_login(user)
            _query_check(
                self.UPDATE_ASSESSMENT_REGISTRY_QUERY,
                update_minput,
                variables={'projectId': self.project1.id, 'assessmentRegistryId': self.assessment_registry.id},
                assert_for_error=True,
                okay=False
            )

        # --- member user
        self.force_login(self.member_user)
        content = _query_check(
            self.UPDATE_ASSESSMENT_REGISTRY_QUERY,
            update_minput,
            variables={'projectId': self.project1.id, 'assessmentRegistryId': self.assessment_registry.id},
            okay=False
        )
        data = content['data']['project']['updateAssessmentRegistry']['result']
        self.assertEqual(data['id'], str(self.assessment_registry.id))
        self.assertEqual(data['bgCrisisType'], update_minput['bgCrisisType'])
        self.assertEqual(data['bgPreparedness'], update_minput['bgPreparedness'])
        self.assertEqual(data['confidentiality'], update_minput['confidentiality'])
        self.assertEqual(data['coordinatedJoint'], update_minput['coordinatedJoint'])
        self.assertEqual(data['status'], update_minput['status'])
        self.assertEqual(data['detailsType'], update_minput['detailsType'])
        self.assertEqual(data['externalSupport'], update_minput['externalSupport'])
        self.assertEqual(data['family'], update_minput['family'])
        self.assertEqual(data['frequency'], update_minput['frequency'])
        self.assertEqual(data['lead']['id'], str(update_minput['lead']))
        self.assertEqual(data['language'], update_minput['language'])
        self.assertEqual(data['bgCountries'][0]['id'], str(update_minput['bgCountries'][0]))


class TestAnalysisMutationSnapShotTestCase(GraphQLSnapShotTestCase):
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
        self.project1 = ProjectFactory.create()
        # leads
        self.lead1, self.lead2 = LeadFactory.create_batch(2, project=self.project1)
        # organizations
        self.organization1, self.organization2 = OrganizationFactory.create_batch(2)
        # region
        self.region = RegionFactory.create()
        self.admin_level1 = AdminLevelFactory.create(region=self.region)
        # geo_areas
        self.geo_area1, self.geo_area2 = GeoAreaFactory.create_batch(2, admin_level=self.admin_level1)
        self.question1 = QuestionFactory.create(
            sector=Question.QuestionSector.RELEVANCE.value,
            sub_sector=Question.QuestionSubSector.RELEVANCE.value,
            question="test question"
        )
        self.file = FileFactory.create()
        self.project1.add_member(self.readonly_member_user, role=self.project_role_reader)
        self.project1.add_member(self.member_user, role=self.project_role_member)
        self.summary_issue1, self.summary_issue2, self.summary_issue3 = SummaryIssueFactory.create_batch(3)
        self.assessment_registry = AssessmentRegistryFactory.create(
            project=self.project1,
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
        self.m_input = dict(
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
        )

    def test_assessment_registry_update(self):
        """
        This test makes sure only valid users can update AssessmentRegistry
        """
        def _query_check(**kwargs):
            return self.query_check(
                self.UPDATE_ASSESSMENT_REGISTRY_QUERY,
                minput=self.m_input,
                variables={'projectId': self.project1.id, 'assessmentRegistryId': self.assessment_registry.id},
                **kwargs
            )

        # -- Without login
        _query_check(assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(assert_for_error=True)

        # --- member user
        # Invalid input
        self.force_login(self.member_user)
        response = _query_check(okay=False)
        self.assertMatchSnapshot(response, 'error')

        # Valid input
        response = _query_check()
        self.assertMatchSnapshot(response, 'success')
