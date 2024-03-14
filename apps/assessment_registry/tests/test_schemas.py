from utils.graphene.tests import GraphQLTestCase

from assessment_registry.factories import AssessmentRegistryFactory
from organization.factories import OrganizationFactory
from geo.factories import RegionFactory
from gallery.factories import FileFactory
from project.factories import ProjectFactory
from user.factories import UserFactory
from lead.factories import LeadFactory
from assessment_registry.factories import (
    QuestionFactory,
    MethodologyAttributeFactory,
    AdditionalDocumentFactory,
    ScoreRatingFactory,
    ScoreAnalyticalDensityFactory,
    AnswerFactory,
    SummaryMetaFactory,
    SummarySubPillarIssueFactory,
    SummaryIssueFactory,
    SummaryFocusFactory,
    SummarySubDimensionIssueFactory,
)
from lead.models import Lead
from project.models import Project
from assessment_registry.models import (
    AssessmentRegistry,
    AdditionalDocument,
    ScoreRating,
    Question,
    SummaryIssue,
)


class TestAssessmentRegistryQuerySchema(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        self.question1 = QuestionFactory.create(
            sector=Question.QuestionSector.RELEVANCE,
            sub_sector=Question.QuestionSubSector.RELEVANCE,
            question='test question'
        )
        self.question2 = QuestionFactory.create(
            sector=Question.QuestionSector.COMPREHENSIVENESS,
            sub_sector=Question.QuestionSubSector.GEOGRAPHIC_COMPREHENSIVENESS,
            question='test question',
        )
        self.country1, self.country2 = RegionFactory.create_batch(2)
        self.organization1, self.organization2 = OrganizationFactory.create_batch(2)
        self.org_list = [self.organization1.id, self.organization2.id]

    def test_assessment_registry_query(self):
        query = '''
            query MyQuery ($projectId: ID! $assessmentRegistryId: ID!) {
              project(id: $projectId) {
                assessmentRegistry (id: $assessmentRegistryId) {
                  id
                  language
                  focuses
                  sectors
                  protectionInfoMgmts
                  protectionRisks
                  lead {
                    id
                  }
                  bgCrisisTypeDisplay
                  bgCountries {
                    id
                  }
                  methodologyAttributes {
                    id
                  }
                  additionalDocuments {
                    id
                    file {
                      file {
                        url
                      }
                    }
                  }
                  scoreRatings {
                    id
                    ratingDisplay
                    scoreTypeDisplay
                  }
                  scoreAnalyticalDensity {
                    id
                  }
                  cna {
                    answer
                    id
                    question {
                      id
                    }
                  }

                   summaryDimensionMeta {
                      id
                   }
                   summarySubDimensionIssue {
                      id
                   }
                   summaryPillarMeta {
                      id
                   }
                   summarySubPillarIssue {
                      id
                   }
                   metadataComplete
                   cnaComplete
                }
              }
            }
        '''

        project1 = ProjectFactory.create(status=Project.Status.ACTIVE)

        member_user = UserFactory.create()
        non_member_user = UserFactory.create()

        lead_1 = LeadFactory.create(project=project1)
        summary_issue1, summary_issue2 = SummaryIssueFactory.create_batch(2)

        project1.add_member(member_user)
        assessment_registry = AssessmentRegistryFactory.create(
            project=project1,
            lead=lead_1,
            confidentiality=AssessmentRegistry.ConfidentialityType.UNPROTECTED,
            bg_countries=[self.country1.id, self.country2.id],
            metadata_complete=True,
            cna_complete=False,
            protection_risks=[
                AssessmentRegistry.ProtectionRiskType.ABDUCATION_KIDNAPPING,
                AssessmentRegistry.ProtectionRiskType.ATTACKS_ON_CIVILIANS
            ],
        )

        methodology_attribute1, methodology_attribute2 = MethodologyAttributeFactory.create_batch(
            2, assessment_registry=assessment_registry
        )

        # Add some additional Document
        AdditionalDocumentFactory.create(
            assessment_registry=assessment_registry,
            document_type=AdditionalDocument.DocumentType.ASSESSMENT_DATABASE,
            file=FileFactory()
        )
        # Add Score Ratings
        ScoreRatingFactory.create(
            assessment_registry=assessment_registry,
            score_type=ScoreRating.ScoreCriteria.RELEVANCE,
            rating=ScoreRating.RatingType.GOOD
        )
        ScoreRatingFactory.create(
            assessment_registry=assessment_registry,
            score_type=ScoreRating.ScoreCriteria.TIMELINESS,
            rating=ScoreRating.RatingType.GOOD
        )
        ScoreRatingFactory.create(
            assessment_registry=assessment_registry,
            score_type=ScoreRating.ScoreCriteria.GRANULARITY,
            rating=ScoreRating.RatingType.GOOD
        )
        # Add Score Analytical Density
        ScoreAnalyticalDensityFactory.create(
            assessment_registry=assessment_registry,
            sector=AssessmentRegistry.SectorType.FOOD_SECURITY,
        )
        ScoreAnalyticalDensityFactory.create(
            assessment_registry=assessment_registry,
            sector=AssessmentRegistry.SectorType.SHELTER,
        )
        # Add Answer to the question
        AnswerFactory.create(
            assessment_registry=assessment_registry,
            question=self.question1,
            answer=True
        )
        AnswerFactory.create(
            assessment_registry=assessment_registry,
            question=self.question2,
            answer=False
        )
        SummaryMetaFactory.create(
            assessment_registry=assessment_registry,
        )
        SummarySubPillarIssueFactory.create(
            assessment_registry=assessment_registry,
            summary_issue=summary_issue1,
            order=1,
        )
        SummaryFocusFactory.create(
            assessment_registry=assessment_registry,
            sector=AssessmentRegistry.SectorType.FOOD_SECURITY,
        )
        SummarySubDimensionIssueFactory.create(
            assessment_registry=assessment_registry,
            summary_issue=summary_issue2,
            sector=AssessmentRegistry.SectorType.FOOD_SECURITY,
            order=1,
        )

        def _query_check(assessment_registry, **kwargs):
            return self.query_check(
                query,
                variables={
                    'projectId': project1.id,
                    'assessmentRegistryId': assessment_registry.id
                }, **kwargs)

        # -- non member user
        self.force_login(non_member_user)
        content1 = _query_check(assessment_registry)
        self.assertIsNone(content1['data']['project']['assessmentRegistry'])

        # --- member user
        self.force_login(member_user)
        content = _query_check(assessment_registry)
        self.assertIsNotNone(content['data']['project']['assessmentRegistry']['id'])
        self.assertEqual(content['data']['project']['assessmentRegistry']['lead']['id'], str(lead_1.id), )
        self.assertIsNotNone(content['data']['project']['assessmentRegistry']['bgCountries'])
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['bgCountries']), 2)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['methodologyAttributes']), 2)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['additionalDocuments']), 1)
        self.assertIsNotNone(
            content['data']['project']['assessmentRegistry']['additionalDocuments'][0]['file']['file']['url']
        )
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['scoreRatings']), 3)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['scoreAnalyticalDensity']), 2)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['cna']), 2)

        self.assertEqual(len(content['data']['project']['assessmentRegistry']['summaryPillarMeta']), 1)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['summarySubPillarIssue']), 1)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['summaryDimensionMeta']), 1)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['summarySubDimensionIssue']), 1)
        self.assertEqual(content['data']['project']['assessmentRegistry']['cnaComplete'], False)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['protectionRisks']), 2)

    def test_list_assessment_registry_query(self):
        query = '''
          query MyQuery ($id: ID!) {
              project(id: $id) {
                  assessmentRegistries {
                      page
                      pageSize
                      totalCount
                      results {
                        id
                      }
                    }
                  }
                }
          '''

        project1 = ProjectFactory.create()
        project2 = ProjectFactory.create()

        member_user = UserFactory.create()
        non_member_user = UserFactory.create()
        non_confidential_member_user = UserFactory.create()

        project1.add_member(member_user)
        project1.add_member(non_confidential_member_user, role=self.project_role_reader_non_confidential)

        lead3, lead4, lead5 = LeadFactory.create_batch(3, project=project1)
        confidential_lead = LeadFactory.create(project=project2, confidentiality=Lead.Confidentiality.CONFIDENTIAL)

        leads = [lead3, lead4, lead5]

        assessment_registries = []
        for i in range(len(leads)):
            assessment_reg = AssessmentRegistryFactory.create(
                project=project1,
                lead=leads[i],
                confidentiality=AssessmentRegistry.ConfidentialityType.UNPROTECTED,
                bg_countries=[self.country1.id, self.country2.id],
            )
            assessment_registries.append(assessment_reg)

        AssessmentRegistryFactory.create(
            project=project1,
            lead=confidential_lead,
            confidentiality=AssessmentRegistry.ConfidentialityType.CONFIDENTIAL,
            bg_countries=[self.country1.id, self.country2.id],
        )

        def _query_check(**kwargs):
            return self.query_check(
                query,
                variables={
                    'id': project1.id,
                }, **kwargs)

        # -- Without login
        _query_check(assert_for_error=True)

        # -- non member user
        self.force_login(non_member_user)
        content = _query_check(okay=False)
        self.assertEqual(content['data']['project']['assessmentRegistries']['totalCount'], 0)

        # -- With login
        self.force_login(member_user)
        content = _query_check(okay=False)

        self.assertEqual(content['data']['project']['assessmentRegistries']['totalCount'], 4, content)

        # -- non confidential member user
        self.force_login(non_confidential_member_user)
        content = _query_check(okay=False)
        self.assertEqual(content['data']['project']['assessmentRegistries']['totalCount'], 3)

    def test_issue_list_query_filter(self):
        query = '''
            query MyQuery (
                $isParent: Boolean
                $label: String
            ) {
            assessmentRegSummaryIssues(
                isParent: $isParent
                label: $label
                ) {
                results {
                    id
                    level
                    childCount
                }
            }
        }
        '''

        member_user = UserFactory.create()
        self.force_login(member_user)

        parent_issue1, parent_issue2, parent_issue3 = SummaryIssueFactory.create_batch(3, parent=None)
        child_issue1 = SummaryIssueFactory.create(parent=parent_issue1)
        child_issue2, child_issue3 = SummaryIssueFactory.create_batch(2, parent=parent_issue2)

        for filter_data, expected_issues in [
            ({}, [child_issue1, child_issue2, child_issue3, parent_issue1, parent_issue2, parent_issue3]),
            ({'isParent': True}, [parent_issue1, parent_issue2, parent_issue3]),
            ({'isParent': False}, [child_issue1, child_issue2, child_issue3]),
        ]:
            content = self.query_check(query, variables={**filter_data})

            self.assertListIds(
                content['data']['assessmentRegSummaryIssues']['results'], expected_issues,
                {'response': content, 'filter': filter_data}
            )

        #  check for child count
        content = self.query_check(query)['data']['assessmentRegSummaryIssues']['results']
        parents = [str(parent.id) for parent in SummaryIssue.objects.filter(parent=None)]
        child_count_list = [item['childCount'] for item in content if item['id'] in parents]
        self.assertEqual(child_count_list, [1, 2, 0])

        #  check for level
        self.assertEqual(set([item['level'] for item in content if item['id'] in parents]), {1})
        self.assertEqual(set([item['level'] for item in content if item['id'] not in parents]), {2})
