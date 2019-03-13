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

    def test_meta_api_no_file(self):
        url = 'api/v1/meta-extraction/1000/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_404(response)

    def test_public_file_api_no_post(self):
        url = '/public-file/'
        self.authenticate()
        response = self.client.post(url)
        self.assert_405(response)

    def test_get_file_public_no_random_string(self):
        url = '/public-file/1/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_404(response)

    def test_get_file_public_invalid_random_string(self):
        url = '/public-file/{}/{}/'
        file_id = self.save_file_with_api()
        file = File.objects.get(id=file_id)
        self.authenticate()
        response = self.client.get(url.format(file.id, 'randomstr'))
        self.assert_404(response)

    def test_get_file_public_valid_random_string(self):
        url = '/public-file/{}/{}/'

        file_id = self.save_file_with_api()
        file = File.objects.get(id=file_id)

        self.authenticate()
        formatted_url = url.format(file_id, file.get_random_string())
        response = self.client.get(formatted_url)
        assert response.status_code == 302, "Should return 302"

    def save_file_with_api(self):
        url = '/api/v1/files/'

        data = {
            'title': 'Test file',
            'file': open(self.supported_file, 'rb'),
            'isPublic': True,
        }

        self.authenticate()
        response = self.client.post(url, data, format='multipart')
        self.assert_201(response)
        return response.data['id']

    # NOTE: Test for files
