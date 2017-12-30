from rest_framework import status
from rest_framework.test import APITestCase
from user.tests.test_apis import AuthMixin

from gallery.models import File, FilePreview
from django.conf import settings

import os
import tempfile


class GalleryTests(AuthMixin, APITestCase):
    """
    Gallery Tests
    """
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION header
        Create temp file
        """
        self.auth = self.get_auth()
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.write(b'Hello world')
        tmp_file.close()

        path = os.path.join(settings.TEST_DIR, 'documents')
        self.supported_file = os.path.join(path, 'doc.docx')
        self.unsupported_file = tmp_file.name

    def tearDown(self):
        """
        Delete test file
        """
        os.unlink(self.unsupported_file)

    def test_upload_supported_file(self):
        """
        Test if file uploads successfully
        """

        last_count = File.objects.count()
        url = '/api/v1/files/'

        data = {
            'title': 'Test file',
            'file': open(self.supported_file, 'rb'),
            'isPublic': True,
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(File.objects.count(), last_count + 1)
        self.assertEqual(response.data['title'], data['title'])

        # Let's delete the file from the filesystem to keep
        # things clean
        last = File.objects.last()
        if os.path.isfile(last.file.path):
            os.unlink(last.file.path)

        # TODO Retrive contents from url data['file'] and assert
        # the text data.

    def test_upload_unsupported_file(self):
        """
        Test if file uploads unsuccessfully
        """

        last_count = File.objects.count()
        url = '/api/v1/files/'

        data = {
            'title': 'Test file',
            'file': open(self.unsupported_file, 'rb'),
            'isPublic': True,
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(File.objects.count(), last_count)

    def test_trigger_api(self):
        file = File.objects.create(
            title='Test',
            created_by=self.user,
        )

        url = '/api/v1/file-extraction-trigger/{}/'.format(file.id)
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_preview_api(self):
        file = File.objects.create(
            title='Test',
            created_by=self.user,
        )
        preview = FilePreview.objects.create(file=file, text_extract='dummy')

        url = '/api/v1/file-previews/{}/'.format(preview.id)
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], preview.text_extract)
