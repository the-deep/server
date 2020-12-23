from deep.tests import TestCase
from project.models import Project
from export.models import Export


class ExportTests(TestCase):
    def test_get_export(self):
        export = self.create(Export, exported_by=self.user)
        url = '/api/v1/exports/{}/'.format(export.id)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['title'], export.title)
        self.assertTrue(response.data['pending'])
        self.assertEqual(response.data['exported_by'], self.user.id)

    def test_trigger_api_without_export_permission(self):
        # Create project and modify role to have no export permission
        project = self.create(Project)
        project.add_member(self.user)
        role = project.get_role(self.user)
        assert role is not None
        role.export_permissions = 0
        role.save()

        url = '/api/v1/export-trigger/'
        data = {
            'filters': [
                ['project', project.pk],
            ],
        }

        self.authenticate(self.user)
        response = self.client.post(url, data)
        self.assert_403(response)

        assert Export.objects.count() == 0

    def test_trigger_api_with_export_permission(self):
        url = '/api/v1/export-trigger/'

        # Create project and modify role to have no export permission
        project = self.create(Project)
        project.add_member(self.user)
        role = project.get_role(self.user)
        assert role is not None
        role.export_permissions = 1
        role.save()

        self.authenticate(self.user)
        response = self.client.post(url)
        self.assert_200(response)

        export = Export.objects.get(id=response.data['export_triggered'])
        self.assertTrue(export.pending)
        self.assertEqual(export.exported_by, self.user)

    def test_delete_export(self):
        export = self.create(Export, exported_by=self.user)
        url = '/api/v1/exports/{}/'.format(export.id)

        self.authenticate()
        response = self.client.delete(url)
        self.assert_204(response)  # delete from api

        # check for database
        assert Export.objects.count() == 1  # should not delete from database
        export_data = Export.objects.get(id=export.id)
        self.assertEqual(export_data.id, export.id)
        self.assertEqual(export_data.is_deleted, True)  # should set `is_delted=True`
