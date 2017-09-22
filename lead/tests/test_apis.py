
from os.path import join

from rest_framework import status
from rest_framework.test import APITestCase
from django.conf import settings

from user.tests.auth_mixin import AuthMixin
from project.models import Project
from ..models import Lead


class ProjectMixin():
    """
    Project Related methods
    TODO: Move to project directory
    """
    def create_or_get_project(self, auth, data=None):
        """
        Create new or return recent project
        TODO: Add better data
        """
        project = Project.objects.all().first()
        if not project:
            url = '/api/v1/projects/'
            data = {
                'title': 'test title',
                # 'members': 1,
                # 'regions': 1,
                # 'user_groups': 1,
                'data': {'testKey': 'testValue'},
            } if data is None else data

            response = self.client.post(url, data,
                                        HTTP_AUTHORIZATION=auth,
                                        format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Project.objects.count(), 1)
            self.assertEqual(response.data['title'], data['title'])
            project = Project.objects.all().first()
        return project


class LeadMixin():
    """
    Lead Related methods
    """
    URL = '/api/v1/leads/'

    def create_or_get_lead(self, auth, data=None):
        """
        Create new or return recent lead
        TODO: Add better data
        """
        lead = Lead.objects.all().first()
        if not lead:
            data = {
                'title': 'test title',
                'project': self.create_or_get_project(self.auth).pk,
                'source': 'test source',
                'confidentiality': Lead.UNPROTECTED,
                'status': Lead.PENDING,
                # 'assignee': '',
                # 'published_on': '',
                'text': 'this is some random text',
                'url': 'https://someurl.com',
                'website': 'https://somewebsite.com',
                # 'attachment': 'file',
            } if data is None else data

            response = self.client.post(self.URL, data,
                                        HTTP_AUTHORIZATION=auth)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Project.objects.count(), 1)
            self.assertEqual(response.data['title'], data['title'])
            lead = Lead.objects.all().first()
        return lead

    def lead_upload(self, auth, attach=None):
        """
        Upload attachment to lead
        TODO: Add required attachment
        """
        lead = self.create_or_get_lead(auth)
        url = self.URL+str(lead.pk)+'/'
        with open(join(settings.TEST_DIR, 'geo.json'),
                  'rb') as fp:
            data = {'attachment': fp}
            response = self.client.patch(url, data,
                                         HTTP_AUTHORIZATION=auth)
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class LeadTests(AuthMixin, ProjectMixin, LeadMixin, APITestCase):
    """
    Lead Tests
    """
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

    def test_create_and_update_lead(self):
        """
        Create Or Update Lead Test
        """
        self.create_or_get_lead(self.auth)

    def test_lead_upload(self):
        """
        Lead Upload Test
        """
        self.lead_upload(self.auth)
