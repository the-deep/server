import os
import tempfile

from django.urls import reverse
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from deep.tests import TestCase
from gallery.models import File, FilePreview
from lead.models import Lead
from project.models import Project
from entry.models import Entry


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

    def test_public_private_file_api_no_post(self):
        public_url = '/public-file/'
        private_url = '/private-file/'
        self.authenticate()
        public_resp = self.client.post(public_url)
        private_resp = self.client.post(private_url)
        self.assert_405(public_resp)
        self.assert_405(private_resp)

    def test_get_file_private_no_random_string(self):
        url = '/private-file/1/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_404(response)

    def test_public_to_private_file_url(self):
        urlf_public = '/public-file/{}/{}/{}'

        file_id = self.save_file_with_api()
        file = File.objects.get(id=file_id)

        url = urlf_public.format(
            urlsafe_base64_encode(force_bytes(file_id)).decode(),
            'random-strings-xxyyzz',
            file.title,
        )
        redirect_url = 'http://testserver' + reverse(
            'gallery_private_url',
            kwargs={
                'uuid': file.uuid, 'filename': file.title,
            },
        )
        response = self.client.get(url)
        assert response.status_code == 302, "Should return 302"
        assert response.url == redirect_url, f"Should return {redirect_url}"

    def test_private_file_url(self):
        urlf = '/private-file/{}/{}'

        file_id = self.save_file_with_api({'isPublic': False})
        entry_file_id = self.save_file_with_api({'isPublic': False})
        file = File.objects.get(id=file_id)
        entry_file = File.objects.get(id=entry_file_id)
        file_url = urlf.format(file.uuid, file.title)
        entry_file_url = urlf.format(file.uuid, file.title)

        # Without authentication
        response = self.client.get(file_url)
        assert response.status_code == 403, "Should return 403 forbidden"

        # With authentication but no file access
        self.authenticate()
        response = self.client.get(file_url)
        assert response.status_code == 403, "Should return 403 forbidden"
        response = self.client.get(entry_file_url)
        assert response.status_code == 403, "Should return 403 forbidden"

        # With authentication and with file access (LEAD)
        project = self.create(Project, role=self.admin_role)
        lead = self.create(Lead, project=project)
        lead.attachment = file
        lead.save()
        response = self.client.get(file_url)
        assert response.status_code == 302, "Should return 302 redirect"

        # With authentication and with file access (Entry)
        entry = self.create(Entry, project=project, lead=lead)
        entry.image = entry_file.get_file_url()
        entry.save()
        response = self.client.get(entry_file_url)
        assert response.status_code == 302, "Should return 302 redirect"

    def save_file_with_api(self, kwargs={}):
        url = '/api/v1/files/'

        data = {
            'title': 'Test file',
            'file': open(self.supported_file, 'rb'),
            'isPublic': True,
            **kwargs,
        }

        self.authenticate()
        response = self.client.post(url, data, format='multipart')
        self.assert_201(response)
        return response.data['id']

    # NOTE: Test for files
