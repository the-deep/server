from dateutil.relativedelta import relativedelta

from django.utils import timezone

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
        self.create(Export, exported_by=self.user, status=Export.Status.SUCCESS)
        self.create(Export, exported_by=self.user, status=Export.Status.SUCCESS)
        self.create(Export, exported_by=self.user, status=Export.Status.PENDING)
        self.create(Export, exported_by=self.user, status=Export.Status.FAILURE)

        self.authenticate()
        response = self.client.get(f'/api/v1/exports/?status={Export.Status.PENDING.value}')
        assert response.json()['count'] == 1
        response = self.client.get('/api/v1/exports/')
        assert response.json()['count'] == 4
        response = self.client.get(f'/api/v1/exports/?status={Export.Status.PENDING.value},{Export.Status.FAILURE.value}')
        assert response.json()['count'] == 2

    def test_export_filter_by_type(self):
        types = [
            Export.DataType.ENTRIES,
            Export.DataType.ASSESSMENTS,
            Export.DataType.ASSESSMENTS,
            Export.DataType.PLANNED_ASSESSMENTS,
        ]
        for type in types:
            self.create(Export, exported_by=self.user, type=type)

        self.authenticate()
        response = self.client.get(f'/api/v1/exports/?type={Export.DataType.ASSESSMENTS}')
        assert response.json()['count'] == 2
        response = self.client.get(f'/api/v1/exports/?type={Export.DataType.ASSESSMENTS},{Export.DataType.ENTRIES}')
        assert response.json()['count'] == 3

    def test_export_filter_by_exported_at(self):
        now = timezone.now()
        days = [2, 3, 4, -2]
        for day in days:
            self.update_obj(self.create(Export, exported_by=self.user), exported_at=now + relativedelta(days=day))
        self.update_obj(self.create(Export, exported_by=self.user), exported_at=now)

        params = {'exported_at__gte': now.strftime('%Y-%m-%d%z')}
        url = '/api/v1/exports/'
        self.authenticate()
        respose = self.client.get(url, params)
        self.assert_200(respose)
        self.assertEqual(len(respose.data['results']), 4)

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
                (Export.Status.PENDING, Export.Status.CANCELED),
                (Export.Status.STARTED, Export.Status.CANCELED),
                (Export.Status.SUCCESS, Export.Status.SUCCESS),
                (Export.Status.FAILURE, Export.Status.FAILURE),
                (Export.Status.CANCELED, Export.Status.CANCELED),
        ]:
            export = self.create(Export, status=initial_status, exported_by=self.user, is_archived=False)
            url = '/api/v1/exports/{}/cancel/'.format(export.id)
            # without export.set_task_id('this-is-random-id'), it will not throw error

            self.authenticate()
            response = self.client.post(url)
            self.assert_200(response)
            self.assertEqual(response.data['status'], final_status)
