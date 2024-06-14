from ary.factories import AssessmentFactory
from lead.factories import LeadFactory
from project.factories import ProjectFactory
from user.factories import UserFactory

from utils.graphene.tests import GraphQLTestCase


class TestAssessmentMutation(GraphQLTestCase):
    def test_assessment_delete_mutation(self):
        query = """
            mutation MyMutation ($projectId: ID! $assessmentId: ID!) {
              project(id: $projectId) {
                assessmentDelete(id: $assessmentId) {
                  ok
                  errors
                  result {
                    id
                  }
                }
              }
            }
        """
        project = ProjectFactory.create()
        member_user = UserFactory.create()
        non_member_user = UserFactory.create()
        project.add_member(member_user)

        lead1 = LeadFactory.create(project=project)
        ary = AssessmentFactory.create(project=project, lead=lead1)

        def _query_check(**kwargs):
            return self.query_check(query, variables={"projectId": project.id, "assessmentId": ary.id}, **kwargs)

        # -- Without login
        _query_check(assert_for_error=True)

        # --- member user
        self.force_login(member_user)
        content = _query_check(assert_for_error=False)
        self.assertEqual(content["data"]["project"]["assessmentDelete"]["ok"], True)
        self.assertIdEqual(content["data"]["project"]["assessmentDelete"]["result"]["id"], ary.id)

        # --- non_member user
        self.force_login(non_member_user)
        _query_check(assert_for_error=True)
