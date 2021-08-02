from utils.graphene.tests import GraphQLTestCase

from user.factories import UserFactory
from project.factories import ProjectFactory

from export.models import Export
from export.factories import ExportFactory


class TestExportQuerySchema(GraphQLTestCase):
    def test_export_query(self):
        """
        Test export for project
        """
        query = '''
            query MyQuery ($projectId: ID! $exportId: ID!) {
              project(id: $projectId) {
                export (id: $exportId) {
                  id
                  title
                }
              }
            }
        '''

        project = ProjectFactory.create()
        project2 = ProjectFactory.create()
        user = UserFactory.create()
        user2 = UserFactory.create()
        project.add_member(user, role=self.role_viewer_non_confidential)
        project2.add_member(user2, role=self.role_viewer_non_confidential)
        export = ExportFactory.create(project=project, exported_by=user)
        other_export = ExportFactory.create(project=project2, exported_by=user2)

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

    def test_exports_query(self):
        query = '''
            query MyQuery ($id: ID!) {
              project(id: $id) {
                exports {
                  page
                  pageSize
                  totalCount
                  results {
                    id
                    title
                  }
                }
              }
            }
        '''
        project = ProjectFactory.create()
        project2 = ProjectFactory.create()
        user = UserFactory.create()
        user2 = UserFactory.create()
        project.add_member(user, role=self.role_viewer_non_confidential)
        project2.add_member(user2, role=self.role_viewer_non_confidential)
        ExportFactory.create_batch(6, project=project, exported_by=user)
        ExportFactory.create_batch(8, project=project2, exported_by=user2)

        def _query_check(**kwargs):
            return self.query_check(query, variables={'id': project.id}, **kwargs)

        # --- Without login
        _query_check(assert_for_error=True)

        # --- With login
        self.force_login(user)
        content = _query_check()
        self.assertEqual(content['data']['project']['exports']['totalCount'], 6, content)
        self.assertEqual(len(content['data']['project']['exports']['results']), 6, content)

        # --- With login by user whose has not exported the export
        self.force_login(user2)
        content = _query_check()
        self.assertEqual(content['data']['project']['exports']['totalCount'], 0, content)
        self.assertEqual(len(content['data']['project']['exports']['results']), 0, content)

    def test_exports_type_filter(self):
        query = '''
            query MyQuery ($id: ID!, $type: [String!]) {
              project(id: $id) {
                exports(type: $type){
                  page
                  pageSize
                  totalCount
                  results {
                    id
                    title
                  }
                }
              }
            }
        '''
        project = ProjectFactory.create()
        user = UserFactory.create()
        project.add_member(user, role=self.role_viewer_non_confidential)
        ExportFactory.create_batch(6, project=project, exported_by=user, type=Export.DataType.ENTRIES)
        ExportFactory.create_batch(2, project=project, exported_by=user, type=Export.DataType.ASSESSMENTS)

        def _query_check(**kwargs):
            return self.query_check(
                query,
                variables={
                    'id': project.id,
                    'type': [Export.DataType.ENTRIES.value]
                },
                **kwargs)

        # --- Without login
        _query_check(assert_for_error=True)

        # --- With login
        self.force_login(user)
        content = _query_check()
        self.assertEqual(content['data']['project']['exports']['totalCount'], 6, content)
        self.assertEqual(len(content['data']['project']['exports']['results']), 6, content)

    def test_exports_status_filter(self):
        query = '''
            query MyQuery ($id: ID!, $status: [String!]) {
              project(id: $id) {
                exports(status: $status){
                  page
                  pageSize
                  totalCount
                  results {
                    id
                    title
                  }
                }
              }
            }
        '''
        project = ProjectFactory.create()
        user = UserFactory.create()
        project.add_member(user, role=self.role_viewer_non_confidential)
        ExportFactory.create_batch(4, project=project, exported_by=user, status=Export.Status.PENDING)
        ExportFactory.create_batch(2, project=project, exported_by=user, status=Export.Status.STARTED)
        ExportFactory.create_batch(3, project=project, exported_by=user, status=Export.Status.SUCCESS)

        def _query_check(**kwargs):
            return self.query_check(
                query,
                variables={
                    'id': project.id,
                    'status': [Export.Status.PENDING.value]
                },
                **kwargs)

        # --- Without login
        _query_check(assert_for_error=True)

        # --- With login
        self.force_login(user)
        content = _query_check()
        self.assertEqual(content['data']['project']['exports']['totalCount'], 4, content)
        self.assertEqual(len(content['data']['project']['exports']['results']), 4, content)

        def _query_check(**kwargs):
            # TODO: Use self.genum() instead of .value.
            return self.query_check(
                query,
                variables={
                    'id': project.id,
                    'status': [Export.Status.PENDING.value, Export.Status.STARTED.value]
                },
                **kwargs)

        self.force_login(user)
        content = _query_check()
        self.assertEqual(content['data']['project']['exports']['totalCount'], 6, content)
        self.assertEqual(len(content['data']['project']['exports']['results']), 6, content)
