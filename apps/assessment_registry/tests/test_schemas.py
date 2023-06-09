from utils.graphene.tests import GraphQLTestCase

from assessment_registry.factories import AssessmentRegistryFactory
from organization.factories import OrganizationFactory
from geo.factories import RegionFactory
from gallery.factories import FileFactory
from project.factories import ProjectFactory
from user.factories import UserFactory
from lead.factories import LeadGroupFactory, LeadFactory
from assessment_registry.factories import (
    QuestionFactory,
    MethodologyAttributeFactory,
    AdditionalDocumentFactory,
    ScoreRatingFactory,
    ScoreAnalyticalDensityFactory,
    AnswerFactory,
)
from lead.models import Lead
from project.models import Project
from assessment_registry.models import (
    AssessmentRegistry,
    AdditionalDocument,
    ScoreRating,
    Question,
)


class TestAssessmentRegistryQuerySchema(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        self.question1 = QuestionFactory.create(
            sector=Question.QuestionSector.RELEVANCE,
            sub_sector=Question.QuestionSubSector.RELEVANCE,
        )
        self.question2 = QuestionFactory.create(
            sector=Question.QuestionSector.COMPREHENSIVENESS,
            sub_sector=Question.QuestionSubSector.GEOGRAPHIC_COMPREHENSIVENESS,
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
                  lead {
                    id
                  }
                  leadGroup {
                    id
                  }
                  bgCrisisTypeDisplay
                  bgCountries {
                    id
                  }
                  leadOrganizations {
                    id
                  }
                  nationalPartners {
                      id
                  }
                  internationalPartners {
                      id
                  }
                  governments {
                      id
                  }
                  donors {
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
                }
              }
            }
        '''

        project1 = ProjectFactory.create(status=Project.Status.ACTIVE)

        member_user = UserFactory.create()
        non_member_user = UserFactory.create()

        lead_1 = LeadFactory.create(project=project1)
        lead_group2 = LeadGroupFactory.create(project=project1)

        project1.add_member(member_user)
        assessment_registry = AssessmentRegistryFactory.create(
            project=project1,
            lead=lead_1,
            lead_group=lead_group2,
            confidentiality=AssessmentRegistry.ConfidentialityType.UNPROTECTED,
            bg_countries=[self.country1.id, self.country2.id],
            lead_organizations=self.org_list,
            international_partners=self.org_list,
            donors=self.org_list,
            national_partners=self.org_list,
            governments=self.org_list,
        )

        methodology_attribute1, methodology_attribute2 = MethodologyAttributeFactory.create_batch(
            2, assessment_registry=assessment_registry
        )

        # Add some additional Document
        AdditionalDocumentFactory.create(
            assessment_registry=assessment_registry,
            document_type=AdditionalDocument.DocumentType.EXECUTIVE_SUMMARY,
            file=FileFactory()
        )
        # Add Score Ratings
        ScoreRatingFactory.create(
            assessment_registry=assessment_registry,
            score_type=ScoreRating.ScoreType.RELEVANCE,
            rating=ScoreRating.RatingType.GOOD
        )
        ScoreRatingFactory.create(
            assessment_registry=assessment_registry,
            score_type=ScoreRating.ScoreType.TIMELINESS,
            rating=ScoreRating.RatingType.GOOD
        )
        ScoreRatingFactory.create(
            assessment_registry=assessment_registry,
            score_type=ScoreRating.ScoreType.GRANULARITY,
            rating=ScoreRating.RatingType.GOOD
        )
        # Add Score Analytical Density
        ScoreAnalyticalDensityFactory.create(
            assessment_registry=assessment_registry,
            sector=AssessmentRegistry.SectorType.FOOD,
            value=1
        )
        ScoreAnalyticalDensityFactory.create(
            assessment_registry=assessment_registry,
            sector=AssessmentRegistry.SectorType.SHELTER,
            value=5
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

        def _query_check(assessment_registry, **kwargs):
            return self.query_check(
                query,
                variables={
                    'projectId': project1.id,
                    'assessmentRegistryId': assessment_registry.id
                }, **kwargs)

        # -- non member user (Project 1)
        self.force_login(non_member_user)
        content1 = _query_check(assessment_registry)
        self.assertIsNone(content1['data']['project']['assessmentRegistry'])

        # --- member user
        self.force_login(member_user)
        content = _query_check(assessment_registry)
        self.assertIsNotNone(content['data']['project']['assessmentRegistry']['id'])
        self.assertEqual(content['data']['project']['assessmentRegistry']['lead']['id'], str(lead_1.id), )
        self.assertEqual(content['data']['project']['assessmentRegistry']['leadGroup']['id'], str(lead_group2.id), )
        self.assertIsNotNone(content['data']['project']['assessmentRegistry']['bgCountries'])
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['bgCountries']), 2)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['leadOrganizations']), 2)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['internationalPartners']), 2)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['governments']), 2)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['nationalPartners']), 2)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['donors']), 2)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['methodologyAttributes']), 2)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['additionalDocuments']), 1)
        self.assertIsNotNone(
            content['data']['project']['assessmentRegistry']['additionalDocuments'][0]['file']['file']['url']
        )
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['scoreRatings']), 3)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['scoreAnalyticalDensity']), 2)
        self.assertEqual(len(content['data']['project']['assessmentRegistry']['cna']), 2)

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

        lead_group_confidential = LeadGroupFactory.create(project=project2)
        lead_group3, lead_group4, lead_group5 = LeadGroupFactory.create_batch(3, project=project1)

        leads = [lead3, lead4, lead5]
        lead_groups = [lead_group3, lead_group4, lead_group5]

        assessment_registries = []
        for i in range(len(leads)):
            assessment_reg = AssessmentRegistryFactory.create(
                project=project1,
                lead=leads[i],
                lead_group=lead_groups[i],
                confidentiality=AssessmentRegistry.ConfidentialityType.UNPROTECTED,
                bg_countries=[self.country1.id, self.country2.id],
                lead_organizations=self.org_list,
                international_partners=self.org_list,
                donors=self.org_list,
                national_partners=self.org_list,
                governments=self.org_list,
            )
            assessment_registries.append(assessment_reg)

        AssessmentRegistryFactory.create(
            project=project1,
            lead=confidential_lead,
            lead_group=lead_group_confidential,
            confidentiality=AssessmentRegistry.ConfidentialityType.CONFIDENTIAL,
            bg_countries=[self.country1.id, self.country2.id],
            lead_organizations=self.org_list,
            international_partners=self.org_list,
            donors=self.org_list,
            national_partners=self.org_list,
            governments=self.org_list,
        )

        def _query_check(**kwargs):
            return self.query_check(
                query,
                variables={
                    'id': project1.id,
                }, **kwargs)

        # -- Without login
        _query_check(assert_for_error=True)

        # -- non member user (Project 1)
        self.force_login(non_member_user)
        content = _query_check(okay=False)
        self.assertEqual(content['data']['project']['assessmentRegistries']['totalCount'], 0)

        # -- With login
        self.force_login(member_user)
        content = _query_check(okay=False)

        self.assertEqual(content['data']['project']['assessmentRegistries']['totalCount'], 4, content)

        # -- non confidential member user (Project 1)
        self.force_login(non_confidential_member_user)
        content = _query_check(okay=False)
        self.assertEqual(content['data']['project']['assessmentRegistries']['totalCount'], 3)
