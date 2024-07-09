import os
import tempfile

from analysis_framework.factories import AnalysisFrameworkFactory
from django.urls import reverse
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from entry.factories import EntryAttachmentFactory, EntryFactory
from lead.factories import LeadFactory

from deep.tests import TestCase
from gallery.models import File, FilePreview
from lead.models import Lead
from project.models import Project
from entry.models import Entry
from user.factories import UserFactory
from project.factories import ProjectFactory
from gallery.enums import PrivateFileModuleType
from utils.graphene.tests import GraphQLTestCase


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
        super().tearDown()
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
            urlsafe_base64_encode(force_bytes(file_id)),
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
        assert response.status_code == 302, "Should return 302 redirect"
        # -- Try again with redirect url
        response = self.client.get(response.url)
        assert response.status_code == 403, "Should return 403 forbidden"

        # With authentication but no file access
        self.authenticate()
        response = self.client.get(file_url)
        assert response.status_code == 302, "Should return 302 redirect"
        # -- Try again with redirect url
        response = self.client.get(response.url)
        assert response.status_code == 403, "Should return 403 forbidden"
        response = self.client.get(entry_file_url)
        assert response.status_code == 302, "Should return 302 redirect"
        # -- Try again with redirect url
        response = self.client.get(response.url)
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
        entry.image_raw = entry_file.get_file_url()
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


class PrivateAttachmentFileViewTest(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        # Create a test user

        self.member_user = UserFactory.create()
        self.member_user1 = UserFactory.create()
        self.normal_user = UserFactory.create()
        self.af = AnalysisFrameworkFactory.create()
        # Create a test entry attachment
        # for normal user
        self.project = ProjectFactory.create()
        self.project.add_member(self.member_user1, role=self.project_role_reader_non_confidential)
        # for member user
        self.project1 = ProjectFactory.create()
        self.project1.add_member(self.member_user, role=self.project_role_admin)

        self.lead = LeadFactory.create(project=self.project)
        # UNPROTECTED lead
        self.lead1 = LeadFactory.create(
            project=self.project1,
            confidentiality=Lead.Confidentiality.UNPROTECTED
        )
        # RESTRICTED lead
        self.lead2 = LeadFactory.create(
            project=self.project1,
            confidentiality=Lead.Confidentiality.RESTRICTED
        )
        # CONFIDENTIAL lead
        self.lead3 = LeadFactory.create(
            project=self.project1,
            confidentiality=Lead.Confidentiality.CONFIDENTIAL
        )

        self.attachment = EntryAttachmentFactory.create()
        self.attachment1 = EntryAttachmentFactory.create()
        self.attachment2 = EntryAttachmentFactory.create()
        self.attachment3 = EntryAttachmentFactory.create()
        self.attachment4 = EntryAttachmentFactory.create()

        self.entry = EntryFactory.create(
            analysis_framework=self.af,
            lead=self.lead,
            project=self.project,
            entry_attachment=self.attachment3
        )
        self.entry1 = EntryFactory.create(
            analysis_framework=self.af,
            lead=self.lead1,
            project=self.project1,
            entry_attachment=self.attachment
        )
        self.entry1 = EntryFactory.create(
            analysis_framework=self.af,
            lead=self.lead3,
            project=self.project1,
            entry_attachment=self.attachment1
        )

        self.entry2 = EntryFactory.create(
            analysis_framework=self.af,
            lead=self.lead,
            project=self.project1,
            entry_attachment=self.attachment2
        )

        self.entry3 = EntryFactory.create(
            analysis_framework=self.af,
            lead=self.lead1,
            project=self.project,
            entry_attachment=self.attachment4
        )

        self.url1 = reverse('external_private_url', kwargs={
            'module': PrivateFileModuleType.ENTRY_ATTACHMENT.value,
            'identifier': urlsafe_base64_encode(force_bytes(self.entry.id)),
            'filename': "test.pdf"
        })

        self.url2 = reverse('external_private_url', kwargs={
            'module': PrivateFileModuleType.ENTRY_ATTACHMENT.value,
            'identifier': urlsafe_base64_encode(force_bytes(self.entry1.id)),
            'filename': "test.pdf"
        })

        self.url3 = reverse('external_private_url', kwargs={
            'module': PrivateFileModuleType.ENTRY_ATTACHMENT.value,
            'identifier': urlsafe_base64_encode(force_bytes(self.entry2.id)),
            'filename': "test.pdf"
        })

        self.url4 = reverse('external_private_url', kwargs={
            'module': PrivateFileModuleType.ENTRY_ATTACHMENT.value,
            'identifier': urlsafe_base64_encode(force_bytes(self.entry.id)),
            'filename': "test.pdf"
        })

        self.url5 = reverse('external_private_url', kwargs={
            'module': PrivateFileModuleType.ENTRY_ATTACHMENT.value,
            'identifier': urlsafe_base64_encode(force_bytes(self.entry3.id)),
            'filename': "test.pdf"
        })

    def test_without_login(self):
        response = self.client.get(self.url1)
        self.assertEqual(401, response.status_code)

    def test_access_by_normal_user(self):
        self.force_login(self.normal_user)
        response = self.client.get(self.url2)
        self.assertEqual(403, response.status_code)

    def test_access_by_non_member_user(self):
        self.force_login(self.member_user)
        response = self.client.get(self.url4)
        self.assertEqual(403, response.status_code)

    def test_access_by_member_user(self):
        self.force_login(self.member_user)
        response = self.client.get(self.url2)
        self.assertEqual(302, response.status_code)

    def test_with_memeber_non_confidential_access(self):
        self.force_login(self.member_user1)
        response = self.client.get(self.url5)
        self.assertEqual(302, response.status_code)

    def test_access_forbidden(self):
        self.force_login(self.member_user)
        invalid_url = reverse('external_private_url', kwargs={
            'module': PrivateFileModuleType.ENTRY_ATTACHMENT.value,
            'identifier': urlsafe_base64_encode(force_bytes(999999)),
            'filename': 'test.pdf'
        })
        response = self.client.get(invalid_url)
        self.assertEqual(404, response.status_code)
