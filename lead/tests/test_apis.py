from rest_framework import status
from rest_framework.test import APITestCase

from user.tests.test_apis import AuthMixin
from project.tests.test_apis import ProjectMixin
from lead.models import Lead


class LeadMixin():
    """
    Lead Related methods
    Required Mixins: ProjectMixin [project.tests.test_apis]
    """
    def create_or_get_lead(self):
        """
        Create new or return recent lead
        """
        lead = Lead.objects.first()
        if not lead:
            lead = Lead.objects.create(
                title='Test lead',
                project=self.create_or_get_project(),
                source='Test source',
                confidentiality=Lead.UNPROTECTED,
                status=Lead.PENDING,
                text='Random text',
            )

        return lead


class LeadTests(AuthMixin, ProjectMixin, LeadMixin, APITestCase):
    """
    Lead Tests
    """
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

    def test_create_lead(self):
        """
        Create Lead Test
        """

        url = '/api/v1/leads/'
        data = {
            'title': 'test title',
            'project': self.create_or_get_project().pk,
            'source': 'test source',
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
            'text': 'this is some random text',
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(response.data['title'], data['title'])

    def test_options(self):
        """
        Options api
        """
        url = '/api/v1/lead-options/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_trigger_api(self):
        """
        We can't really test for background tasks that happen in separate
        process.

        So create a dummy test and perform actual test in test_tasks
        """
        lead = self.create_or_get_lead()
        url = '/api/v1/lead-extraction-trigger/{}/'.format(lead.id)
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
