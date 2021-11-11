from utils.graphene.tests import GraphQLTestCase

from user.factories import UserFactory
from project.factories import ProjectFactory
from export.factories import ExportFactory

from export.models import Export


class TestExportMutationSchema(GraphQLTestCase):
    CREATE_EXPORT_QUERY = '''
        mutation MyMutation ($projectId: ID!, $input: ExportCreateInputType!) {
          project(id: $projectId) {
            exportCreate(data: $input) {
              ok
              errors
              result {
                id
                title
                type
                status
                pending
                mimeType
                isPreview
                isArchived
                format
                filters
                file
                exportedAt
                exportType
                project
                exportedBy {
                  id
                  displayName
                }
              }
            }
          }
        }
    '''

    CANCEL_EXPORT_QUERY = '''
        mutation MyMutation ($projectId: ID!, $exportId: ID!) {
          project(id: $projectId) {
            exportCancel(id: $exportId) {
              ok
              errors
              result {
                id
                title
                type
                status
                pending
                mimeType
                isPreview
                isArchived
                format
                filters
                file
                exportedAt
                exportType
                project
                exportedBy {
                  id
                  displayName
                }
              }
            }
          }
        }
    '''

    DELETE_EXPORT_QUERY = '''
        mutation MyMutation ($projectId: ID!, $exportId: ID!) {
          project(id: $projectId) {
            exportDelete(id: $exportId) {
              ok
              errors
              result {
                id
                title
                type
                status
                pending
                mimeType
                isPreview
                isArchived
                format
                filters
                file
                exportedAt
                exportType
                project
                exportedBy {
                  id
                  displayName
                }
              }
            }
          }
        }
    '''

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        # User with role
        self.non_member_user = UserFactory.create()
        self.readonly_member_user = UserFactory.create()
        self.member_user = UserFactory.create()
        self.another_member_user = UserFactory.create()
        self.project.add_member(self.readonly_member_user, role=self.project_role_viewer_non_confidential)
        self.project.add_member(self.member_user, role=self.project_role_analyst)
        self.project.add_member(self.another_member_user, role=self.project_role_analyst)
        self.common_export_attrs = dict(
            project=self.project,
            format=Export.Format.DOCX,
            type=Export.DataType.ENTRIES,
            export_type=Export.ExportType.REPORT,
        )

    def test_export_create(self):
        """
        This test makes sure only valid users can create export
        """
        def _query_check(minput, **kwargs):
            return self.query_check(
                self.CREATE_EXPORT_QUERY,
                minput=minput,
                variables={'projectId': self.project.id},
                **kwargs
            )

        minput = dict(
            format=self.genum(Export.Format.PDF),
            type=self.genum(Export.DataType.ENTRIES),
            title='Export 101',
            exportType=self.genum(Export.ExportType.EXCEL),
            isPreview=False,
            filters={},
        )
        # -- Without login
        _query_check(minput, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(minput, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(minput, assert_for_error=True)

        # --- member user
        self.force_login(self.member_user)
        # ----- (Simple validation)
        response = _query_check(minput, okay=False)['data']
        self.assertEqual(response['project']['exportCreate']['result'], None, response)

        # -----
        minput['format'] = self.genum(Export.Format.XLSX)
        response = _query_check(minput)['data']
        self.assertNotEqual(response['project']['exportCreate']['result'], None, response)

    def test_export_cancel(self):
        """
        This test makes sure only valid users can cancel export
        """
        def _query_check(export, **kwargs):
            return self.query_check(
                self.CANCEL_EXPORT_QUERY,
                variables={'projectId': self.project.id, 'exportId': export.id},
                **kwargs
            )

        export_pending = ExportFactory.create(
            exported_by=self.member_user, status=Export.Status.PENDING, **self.common_export_attrs)
        export_failed = ExportFactory.create(
            exported_by=self.member_user, status=Export.Status.FAILURE, **self.common_export_attrs)
        export2 = ExportFactory.create(exported_by=self.another_member_user, **self.common_export_attrs)

        # -- Without login
        _query_check(export_pending, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(export_pending, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(export_pending, assert_for_error=True)

        # --- member user (but not owner)
        self.force_login(self.member_user)
        _query_check(export2, assert_for_error=True)

        # --- member user (with ownership)
        self.force_login(self.member_user)
        content = _query_check(export_failed)['data']['project']['exportCancel']['result']
        self.assertEqual(content['status'], self.genum(Export.Status.FAILURE), content)

        content = _query_check(export_pending)['data']['project']['exportCancel']['result']
        self.assertEqual(content['status'], self.genum(Export.Status.CANCELED), content)

    def test_export_delete(self):
        """
        This test makes sure only valid users can delete export
        """
        def _query_check(export, **kwargs):
            return self.query_check(
                self.DELETE_EXPORT_QUERY,
                variables={'projectId': self.project.id, 'exportId': export.id},
                **kwargs
            )

        export1 = ExportFactory.create(exported_by=self.member_user, **self.common_export_attrs)
        export2 = ExportFactory.create(exported_by=self.another_member_user, **self.common_export_attrs)

        # -- Without login
        _query_check(export1, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(export1, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(export1, assert_for_error=True)

        # --- member user (but not owner)
        self.force_login(self.member_user)
        _query_check(export2, assert_for_error=True)

        # --- member user (with ownership)
        self.force_login(self.member_user)
        content = _query_check(export1)['data']['project']['exportDelete']['result']
        self.assertEqual(content['id'], str(export1.id), content)
