from utils.graphene.tests import GraphQLTestCase

from user.factories import UserFactory
from project.factories import ProjectFactory

from analysis.models import Analysis
from analysis.factories import AnalysisFactory


class TestAnalysisQuerySchema(GraphQLTestCase):
    def test_analysis_query(self):
        """
        Test analysis for project
        """
        query = '''
            query MyQuery ($projectId: ID! $exportId: ID!) {
              project(id: $projectId) {
                analysis (id: $exportId) {
                  id
                  title
                }
              }
            }
        '''

        member = UserFactory.create()
        non_member = UserFactory.create()
        project = ProjectFactory.create()
        project.add_member(member, role=self.project_role_viewer_non_confidential)
        analysis = AnalysisFactory.create(project=project)

        def _query_check(export, **kwargs):
            return self.query_check(query, variables={'projectId': project.id, 'exportId': export.id}, **kwargs)

        # -- Without login
        _query_check(export, assert_for_error=True)

        # --- With login
        self.force_login(user)
        content = _query_check(export)
        self.assertNotEqual(content['data']['project']['export'], None, content)
        self.assertEqual(content['data']['project']['export']['id'], str(export.id))

        self.force_login(user)
        content = _query_check(other_export)
        self.assertEqual(content['data']['project']['export'], None, content)
