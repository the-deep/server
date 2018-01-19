from rest_framework import status
from rest_framework.test import APITestCase

from user.tests.test_apis import AuthMixin
from export.models import Export


class ExportTests(AuthMixin, APITestCase):
    """
    Export Tests
    """
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

    def test_get_export(self):
        export = Export.objects.create(
            title='tmp',
            exported_by=self.user,
        )

        url = '/api/v1/exports/{}/'.format(export.id)
        response = self.client.get(url,
                                   HTTP_AUTHORIZATION=self.auth,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], export.title)
        self.assertTrue(response.data['pending'])
        self.assertEqual(response.data['exported_by'], self.user.id)

    def test_trigger_api(self):
        url = '/api/v1/export-trigger/'

        response = self.client.post(url,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        export = Export.objects.get(id=response.data['export_triggered'])
        self.assertTrue(export.pending)
        self.assertEqual(export.exported_by, self.user)
