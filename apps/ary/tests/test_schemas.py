from utils.graphene.tests import GraphQLTestCase

from lead.models import Lead

from ary.factories import AssessmentFactory
from project.factories import ProjectFactory
from lead.factories import LeadFactory
from user.factories import UserFactory


class TestAssessmentQuery(GraphQLTestCase):
    def test_assessment_query(self):
        query = '''
              query MyQuery ($id: ID!) {
                project(id: $id) {
                  assessments(ordering: "id") {
                    results {
                      id
                      score
                      metadata
                      summary
                      leadGroup {
                          id
                      }
                      lead {
                          id
                      }
                      questionnaire
                      project {
                        id
                      }
                    }
                    totalCount
                  }
                }
              }
        '''
        project1 = ProjectFactory.create()
        project2 = ProjectFactory.create()
        member_user = UserFactory.create()
        member_user = UserFactory.create()
        non_confidential_member_user = UserFactory.create()
        project1.add_member(non_confidential_member_user, role=self.project_role_reader_non_confidential)
        non_member_user = UserFactory.create()
        project1.add_member(member_user)
        project2.add_member(member_user)

        lead1 = LeadFactory.create(project=project1, confidentiality=Lead.Confidentiality.CONFIDENTIAL)
        lead2 = LeadFactory.create(project=project1)
        lead3 = LeadFactory.create(project=project2)
        ary1 = AssessmentFactory.create(project=project1, lead=lead1)
        ary2 = AssessmentFactory.create(project=project1, lead=lead2)
        ary3 = AssessmentFactory.create(project=project2, lead=lead3)

        # -- non member user (Project 1)
        self.force_login(non_member_user)
        content = self.query_check(query, variables={'id': project1.id})
        self.assertEqual(content['data']['project']['assessments']['totalCount'], 0)
        self.assertListIds(content['data']['project']['assessments']['results'], [], content)

        # -- non confidential member user (Project 1)
        self.force_login(non_confidential_member_user)
        content = self.query_check(query, variables={'id': project1.id})
        self.assertEqual(content['data']['project']['assessments']['totalCount'], 1)
        self.assertListIds(content['data']['project']['assessments']['results'], [ary2], content)

        # -- member user (Project 1)
        self.force_login(member_user)
        content = self.query_check(query, variables={'id': project1.id})
        self.assertEqual(content['data']['project']['assessments']['totalCount'], 2)
        self.assertListIds(content['data']['project']['assessments']['results'], [ary1, ary2], content)

        # -- member user (Project 2)
        content = self.query_check(query, variables={'id': project2.id})
        self.assertEqual(content['data']['project']['assessments']['totalCount'], 1)
        self.assertEqual(content['data']['project']['assessments']['results'][0]['id'], str(ary3.id))
