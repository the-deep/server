from deep.tests import TestCase
from gallery.models import File, FilePreview
from django.conf import settings

import os
import tempfile


class GalleryTests(TestCase):
    def setUp(self):
        super().setUp()

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.write(b'Hello world')
        tmp_file.close()

        path = os.path.join(settings.TEST_DIR, 'documents')
        self.supported_file = os.path.join(path, 'doc.docx')
        self.unsupported_file = tmp_file.name

    def tearDown(self):
        os.unlink(self.unsupported_file)

    def test_upload_supported_file(self):
        file_count = File.objects.count()
        url = '/api/v1/files/'

        data = {
            'title': 'Test file',
            'file': open(self.supported_file, 'rb'),
            'isPublic': True,
        }

        self.authenticate()
        response = self.client.post(url, data, format='multipart')
        self.assert_201(response)

        self.assertEqual(File.objects.count(), file_count + 1)
        self.assertEqual(response.data['title'], data['title'])

        # Let's delete the file from the filesystem to keep
        # things clean
        last = File.objects.last()
        if os.path.isfile(last.file.path):
            os.unlink(last.file.path)

        # TODO Retrive contents from url data['file'] and assert
        # the text data.

    def test_upload_unsupported_file(self):
        file_count = File.objects.count()
        url = '/api/v1/files/'

        data = {
            'title': 'Test file',
            'file': open(self.unsupported_file, 'rb'),
            'isPublic': True,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_400(response)

        self.assertEqual(File.objects.count(), file_count)

    def test_trigger_api(self):
        url = '/api/v1/file-extraction-trigger/'
        data = {
            'file_ids': [1],
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_200(response)

        self.assertTrue(FilePreview.objects.filter(
            id=response.data['extraction_triggered']
        ).exists())

    def test_duplicate_trigger_api(self):
        preview = self.create(FilePreview, file_ids=[1, 2])
        url = '/api/v1/file-extraction-trigger/'
        data = {
            'file_ids': [2, 1],
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_200(response)

        self.assertEqual(response.data['extraction_triggered'], preview.id)

    def test_preview_api(self):
        preview = self.create(FilePreview, file_ids=[])
        url = '/api/v1/file-previews/{}/'.format(preview.id)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['text'], preview.text)
