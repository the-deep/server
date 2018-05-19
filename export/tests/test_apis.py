from deep.tests import TestCase
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

    def test_trigger_api(self):
        url = '/api/v1/export-trigger/'

        self.authenticate()
        response = self.client.post(url)
        self.assert_200(response)

        export = Export.objects.get(id=response.data['export_triggered'])
        self.assertTrue(export.pending)
        self.assertEqual(export.exported_by, self.user)
