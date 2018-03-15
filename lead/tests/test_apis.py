from rest_framework import status
from rest_framework.test import APITestCase

from user.tests.test_apis import AuthMixin
from project.tests.test_apis import ProjectMixin
from project.models import Project, ProjectMembership
from geo.models import Region
from lead.models import Lead

import logging

from datetime import date

logger = logging.getLogger(__name__)


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
        lead_count = Lead.objects.count()
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
        self.assertEqual(Lead.objects.count(), lead_count + 1)
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

    def test_multiple_project(self):
        """
        Test adding same lead to multiple project
        """
        project1 = Project.objects.create(title='test project')
        ProjectMembership.objects.create(member=self.user, project=project1,
                                         role='normal')
        project2 = Project.objects.create(title='test project')
        ProjectMembership.objects.create(member=self.user, project=project2,
                                         role='normal')

        lead_count = Lead.objects.count()

        url = '/api/v1/leads/'
        data = {
            'title': 'test title',
            'project': [project1.id, project2.id],
            'source': 'test source',
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
            'text': 'this is some random text',
        }

        response = self.client.post(url, data,
                                    format='json',
                                    HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lead.objects.count(), lead_count + 2)

        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0].get('project'), project1.id)
        self.assertEqual(response.data[1].get('project'), project2.id)


# Data to use for testing web info extractor
# Including, url of the page and its attributes:
# source, country, date, website

SAMPLE_WEB_INFO_URL = 'https://reliefweb.int/report/yemen/yemen-emergency-food-security-and-nutrition-assessment-efsna-2016-preliminary-results' # noqa
SAMPLE_WEB_INFO_SOURCE = 'World Food Programme, UN Children\'s Fund, Food and Agriculture Organization of the United Nations' # noqa
SAMPLE_WEB_INFO_COUNTRY = 'Yemen'
SAMPLE_WEB_INFO_DATE = date(2017, 1, 26)
SAMPLE_WEB_INFO_WEBSITE = 'reliefweb.int'
SAMPLE_WEB_INFO_TITLE = 'Yemen Emergency Food Security and Nutrition Assessment (EFSNA) 2016 - Preliminary Results' # noqa


class WebInfoExtractionTests(AuthMixin, APITestCase):
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

        # Create a sample project containing the sample country
        self.sample_region = Region.objects.create(
            code='TEST',
            title=SAMPLE_WEB_INFO_COUNTRY,
            public=True,
            created_by=self.user,
        )
        self.sample_project = Project.objects.create(
            title='Test project',
            created_by=self.user,
        )
        ProjectMembership.objects.create(
            project=self.sample_project,
            member=self.user,
            role='normal',
        )
        self.sample_project.regions.add(self.sample_region)

    def show_warning(self, message=None):
        border_len = 50
        logger.warning('*' * border_len)
        logger.warning('---- Web Extraction Test Not Working ----')
        logger.warning(message)
        logger.warning('*' * border_len)

    def test_extract_web_info(self):
        url = '/api/v1/web-info-extract/'
        data = {
            'url': SAMPLE_WEB_INFO_URL
        }

        try:
            response = self.client.post(url, data,
                                        format='json',
                                        HTTP_AUTHORIZATION=self.auth)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        except Exception:
            self.show_warning('Connection Error')
            return

        expected = {
            'project': self.sample_project.id,
            'date': SAMPLE_WEB_INFO_DATE,
            'country': SAMPLE_WEB_INFO_COUNTRY,
            'website': SAMPLE_WEB_INFO_WEBSITE,
            'title': SAMPLE_WEB_INFO_TITLE,
            'url': SAMPLE_WEB_INFO_URL,
            'source': SAMPLE_WEB_INFO_SOURCE,
        }
        self.assertEqual(response.data, expected)
