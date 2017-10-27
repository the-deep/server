from rest_framework import status
from rest_framework.test import APITestCase
from user.tests.test_apis import AuthMixin

from gallery.models import File

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
        self.file = tmp_file.name

    def tearDown(self):
        """
        Delete test file
        """
        os.unlink(self.file)

    def test_upload_file(self):
        """
        Test if file uploads successfully
        """

        last_count = File.objects.count()
        url = '/api/v1/files/'

        data = {
            'title': 'Test file',
            'file': open(self.file, 'rb'),
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
            os.remove(last.file.path)

        # TODO Retrive contents from url data['file'] and assert
        # the text data.
