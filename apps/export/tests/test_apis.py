from django.core.cache import cache

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
        user1 = self.create_user()
        user2 = self.create_user()

        export1 = self.create(Export, exported_by=user1)
        export2 = self.create(Export, exported_by=user2)
        export3 = self.create(Export, exported_by=user1)

        before_delete = Export.objects.count()
        # test user can delete his export
        url = '/api/v1/exports/{}/'.format(export1.id)

        self.authenticate(user1)
        response = self.client.delete(url)
        self.assert_204(response)  # delete from api

        # test user canot delete other export
        url = '/api/v1/exports/{}/'.format(export3.id)

        self.authenticate(user2)
        response = self.client.delete(url)
        self.assert_404(response)

        url = '/api/v1/exports/{}/'.format(export2.id)
        self.authenticate(user2)
        response = self.client.delete(url)
        self.assert_204(response)

        after_delete = Export.objects.count()
        self.assertEqual(before_delete, after_delete)

        # test get the data from api
        url = '/api/v1/exports/'
        self.authenticate(user1)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data['count'], 1)  # should have one export

        # test update by deleted export
        url = '/api/v1/exports/{}/'.format(export1.id)
        data = {
            'title': 'Title test'
        }
        self.authenticate(user1)
        response = self.client.patch(url, data)
        self.assert_404(response)

        # test update by another user
        url = '/api/v1/exports/{}/'.format(export1.id)
        data = {
            'title': 'Title test'
        }
        self.authenticate(user2)
        response = self.client.patch(url, data)
        self.assert_404(response)

    def test_export_filter_by_status(self):
        self.create(Export, exported_by=self.user, status=Export.SUCCESS)
        self.create(Export, exported_by=self.user, status=Export.SUCCESS)
        self.create(Export, exported_by=self.user, status=Export.PENDING)
        self.create(Export, exported_by=self.user, status=Export.FAILURE)

        self.authenticate()
        response = self.client.get(f'/api/v1/exports/?status={Export.PENDING}')
        assert response.json()['count'] == 1

    def test_export_filter_by_archived(self):
        self.create(Export, exported_by=self.user, is_archived=False)
        self.create(Export, exported_by=self.user, is_archived=False)
        self.create(Export, exported_by=self.user, is_archived=True)
        self.create(Export, exported_by=self.user, is_archived=False)

        self.authenticate()
        response = self.client.get(f'/api/v1/exports/?is_archived={True}')
        assert response.json()['count'] == 1

    def test_export_cancel(self):
        for initial_status, final_status in [
                (Export.PENDING, Export.CANCELED),
                (Export.STARTED, Export.CANCELED),
                (Export.SUCCESS, Export.SUCCESS),
                (Export.FAILURE, Export.FAILURE),
                (Export.CANCELED, Export.CANCELED),
        ]:
            export = self.create(Export, status=initial_status, exported_by=self.user, is_archived=False)
            url = '/api/v1/exports/{}/cancel/'.format(export.id)
            # without export.set_task_id('this-is-random-id'), it will not throw error

            self.authenticate()
            response = self.client.post(url)
            self.assert_200(response)
            self.assertEqual(response.data['status'], final_status)
