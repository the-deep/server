from utils.graphene.tests import GraphQLTestCase

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
        project = ProjectFactory.create()
        project2 = ProjectFactory.create()
        member_user = UserFactory.create()
        project.add_member(member_user)
        project2.add_member(member_user)

        lead1 = LeadFactory.create(project=project)
        lead2 = LeadFactory.create(project=project)
        lead3 = LeadFactory.create(project=project2)
        ary1 = AssessmentFactory.create(project=project, lead=lead1)
        ary2 = AssessmentFactory.create(project=project, lead=lead2)
        ary3 = AssessmentFactory.create(project=project2, lead=lead3)

        self.force_login(member_user)
        content = self.query_check(query, variables={'id': project.id})
        self.assertEqual(content['data']['project']['assessments']['totalCount'], 2)
        self.assertListIds(content['data']['project']['assessments']['results'], [ary1, ary2], content)

        # with different project
        content = self.query_check(query, variables={'id': project2.id})
        self.assertEqual(content['data']['project']['assessments']['totalCount'], 1)
        self.assertEqual(content['data']['project']['assessments']['results'][0]['id'], str(ary3.id))
