from deep.tests import TestCase
from user.models import User
from project.models import Project, ProjectMembership
from geo.models import Region
from lead.models import Lead, LeadPreview

import logging
from datetime import date

logger = logging.getLogger(__name__)


class LeadTests(TestCase):
    def test_create_lead(self, assignee=None):
        lead_count = Lead.objects.count()
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': 'MCU',
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
            'text': 'Alien shapeship has been spotted in the sky',
            'assignee': assignee or self.user.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Lead.objects.count(), lead_count + 1)
        r_data = response.json()
        self.assertEqual(r_data['title'], data['title'])
        self.assertEqual(r_data['assignee'], self.user.id)

    def test_get_lead_check_no_of_entries(self, assignee=None):
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': 'MCU',
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
            'text': 'Alien shapeship has been spotted in the sky',
            'assignee': assignee or self.user.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        url = '/api/v1/leads/'

        response = self.client.get(url)

        r_data = response.json()
        assert 'noOfEntries' in r_data["results"][0]

    def test_create_lead_no_create_role(self, assignee=None):
        lead_count = Lead.objects.count()
        project = self.create(Project, role=self.admin_role)

        test_user = self.create(User)
        project.add_member(test_user, role=self.view_only_role)

        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': 'MCU',
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
            'text': 'Alien shapeship has been spotted in the sky',
            'assignee': assignee or self.user.id,
        }

        self.authenticate(test_user)
        response = self.client.post(url, data)
        self.assert_403(response)

        self.assertEqual(Lead.objects.count(), lead_count)

    def test_delete_lead(self):
        project = self.create(Project, role=self.admin_role)
        lead = self.create(Lead, project=project)
        url = '/api/v1/leads/{}/'.format(lead.id)

        self.authenticate()
        response = self.client.delete(url)
        self.assert_204(response)

    def test_delete_lead_no_perm(self):
        project = self.create(Project, role=self.admin_role)
        lead = self.create(Lead, project=project)
        user = self.create(User)

        project.add_member(user, self.view_only_role)

        url = '/api/v1/leads/{}/'.format(lead.id)

        self.authenticate(user)
        response = self.client.delete(url)
        self.assert_403(response)

    def test_multiple_assignee(self):
        self.test_create_lead([self.user.id])

    def test_update_assignee(self):
        # Since we have multiple assignee supported in the Lead model
        # but currently we have only restricted assignee to single value
        # in the API, check if it works in the `update` request

        project = self.create(Project, role=self.admin_role)
        user = self.create(User)
        self.create(ProjectMembership, project=project, member=user)
        lead = self.create(Lead, project=project)

        url = '/api/v1/leads/{}/'.format(lead.id)
        data = {
            'assignee': user.id,
        }

        self.authenticate()
        response = self.client.patch(url, data)
        self.assert_200(response)

        r_data = response.json()
        self.assertEqual(r_data['assignee'], user.id)
        lead = Lead.objects.get(id=lead.id)
        self.assertEqual(lead.get_assignee().id, user.id)

    def test_options(self):
        url = '/api/v1/lead-options/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

    def test_trigger_api(self):
        project = self.create(Project, role=self.admin_role)
        lead = self.create(Lead, project=project)
        url = '/api/v1/lead-extraction-trigger/{}/'.format(lead.id)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

    def test_multiple_project(self):
        project1 = self.create(Project, role=self.admin_role)
        project2 = self.create(Project, role=self.admin_role)

        lead_count = Lead.objects.count()

        url = '/api/v1/leads/'
        data = {
            'title': 'test title',
            'project': [project1.id, project2.id],
            'source': 'test source',
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
            'text': 'this is some random text',
            'assignee': self.user.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        r_data = response.json()
        self.assertEqual(Lead.objects.count(), lead_count + 2)
        self.assertEqual(len(r_data), 2)

        self.assertEqual(r_data[0].get('project'), project1.id)
        self.assertEqual(r_data[1].get('project'), project2.id)

    def test_url_exists(self):
        project = self.create(Project, role=self.admin_role)
        common_url = 'https://same.com/'
        lead1 = self.create(Lead, source_type='website',
                            project=project,
                            url=common_url)
        lead2 = self.create(Lead, source_type='website',
                            project=project,
                            url='https://different.com/')

        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': 'MCU',
            'source_type': 'website',
            'url': common_url,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_400(response)

        url = '/api/v1/leads/{}/'.format(lead2.id)
        data = {
            'url': common_url,
        }

        response = self.client.patch(url, data)
        self.assert_400(response)

        # This should not be raised while editing same lead

        url = '/api/v1/leads/{}/'.format(lead1.id)
        data = {
            'title': 'Spaceship allegedly spotted in sky'
        }
        response = self.client.patch(url, data)
        self.assert_200(response)

    def test_lead_copy(self):
        url = '/api/v1/lead-copy/'

        # Projects [Source]
        project1s = self.create(Project, title='project1s', role=self.admin_role)
        project2s = self.create(Project, title='project2s', role=self.admin_role)
        project3s = self.create(Project, title='project3s')
        project4s = self.create(Project, title='project1s', role=self.view_only_role)

        # Projects [Destination]
        project1d = self.create(Project, title='project1d')
        project2d = self.create(Project, title='project2d', role=self.admin_role)
        project3d = self.create(Project, title='project2d', role=self.admin_role)
        project4d = self.create(Project, title='project4d', role=self.view_only_role)

        # Leads
        lead1 = self.create(Lead, project=project1s)
        lead2 = self.create(Lead, project=project2s)
        lead3 = self.create(Lead, project=project3s)
        lead4 = self.create(Lead, project=project4s)

        # Request body data [also contains unauthorized projects and leads]
        data = {
            'projects': sorted([project4d.pk, project3d.pk, project2d.pk, project1d.pk, project1s.pk]),
            'leads': sorted([lead3.pk, lead2.pk, lead1.pk, lead4.pk]),
        }
        # data [only contains authorized projects and leads]
        validate_data = {
            'projects': sorted([project3d.pk, project2d.pk, project1s.pk]),
            'leads': sorted([lead4.pk, lead2.pk, lead1.pk]),
        }

        lead_stats = [
            # Project, Original Lead Count, Lead Count After lead-copy
            (project1s, 1, 3),
            (project2s, 1, 1),
            (project3s, 1, 1),
            (project4s, 1, 1),

            (project1d, 0, 0),
            (project2d, 0, 3),
            (project3d, 0, 3),
            (project4d, 0, 0),
        ]

        self.authenticate()
        response = self.client.post(url, data)
        rdata = response.json()
        # Sort the data since we are comparing lists
        sorted_rdata = {
            'projects': sorted(rdata['projects']),
            'leads': sorted(rdata['leads']),
        }
        self.assert_200(response)
        self.assertNotEqual(sorted_rdata, data)
        self.assertEqual(sorted_rdata, validate_data)

        for project, old_lead_count, new_lead_count in lead_stats:
            current_lead_count = Lead.objects.filter(project_id=project.pk).count()
            assert new_lead_count == current_lead_count, f'Project: {project.title} lead count is different'

    def test_lead_order_by_page_count(self):
        # Create lead and lead_previews
        project = self.create(Project)
        project.add_member(self.user)

        lead1 = self.create(Lead, project=project)
        self.create(LeadPreview, lead=lead1, page_count=20)

        lead2 = self.create(Lead, project=project)
        self.create(LeadPreview, lead=lead2, page_count=15)

        lead3 = self.create(Lead, project=project)
        self.create(LeadPreview, lead=lead3, page_count=None)

        # Ascending ordering
        url = '/api/v1/leads/?ordering=,page_count,,'  # this also tests leading/trailing/multiple commas
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        assert len(response.data['results']) == 3, "Three leads created"
        leads = response.data['results']
        assert leads[0]['id'] == lead3.id, "Preview3 has no pages"
        assert leads[1]['id'] == lead2.id, "Preview2 has less pages"
        assert leads[2]['id'] == lead1.id, "Preview1 has more pages"

        # Descending ordering
        url = '/api/v1/leads/?ordering=,-page_count,,'  # this also tests leading/trailing/multiple commas
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        assert len(response.data['results']) == 3, "Three leads created"
        leads = response.data['results']
        assert leads[0]['id'] == lead1.id, "Preview1 has more pages"
        assert leads[1]['id'] == lead2.id, "Preview2 has less pages"
        assert leads[2]['id'] == lead3.id, "Preview3 has no pages"


# Data to use for testing web info extractor
# Including, url of the page and its attributes:
# source, country, date, website

SAMPLE_WEB_INFO_URL = 'https://reliefweb.int/report/yemen/yemen-emergency-food-security-and-nutrition-assessment-efsna-2016-preliminary-results' # noqa
SAMPLE_WEB_INFO_SOURCE = 'World Food Programme, UN Children\'s Fund, Food and Agriculture Organization of the United Nations' # noqa
SAMPLE_WEB_INFO_COUNTRY = 'Yemen'
SAMPLE_WEB_INFO_DATE = date(2017, 1, 26)
SAMPLE_WEB_INFO_WEBSITE = 'reliefweb.int'
SAMPLE_WEB_INFO_TITLE = 'Yemen Emergency Food Security and Nutrition Assessment (EFSNA) 2016 - Preliminary Results' # noqa


class WebInfoExtractionTests(TestCase):
    def test_redhum(self):
        url = '/api/v1/web-info-extract/'
        data = {
            'url': 'https://redhum.org/documento/3227553',
        }
        try:
            self.authenticate()
            response = self.client.post(url, data)
            self.assert_200(response)
            self.assertEqual(response['title'], 'Pregnant women flee lack of maternal health care in Venezuela')
            self.assertEqual(response['date'], '2019-07-23')
            self.assertEqual(response['country'], 'Colombia')
            self.assertEqual(response['website'], 'redhum.org')
            self.assertEqual(response['url'], data['url'])
            self.assertEqual(response['source'], 'UNHCR')
        except Exception:
            import traceback
            logger.warning('\n' + ('*' * 30))
            logger.warning('LEAD WEB INFO EXTRACTION ERROR:')
            logger.warning(traceback.format_exc())
            return

    def test_extract_web_info(self):
        # Create a sample project containing the sample country
        sample_region = self.create(Region, title=SAMPLE_WEB_INFO_COUNTRY,
                                    public=True)
        sample_project = self.create(Project, role=self.admin_role)
        sample_project.regions.add(sample_region)

        url = '/api/v1/web-info-extract/'
        data = {
            'url': SAMPLE_WEB_INFO_URL
        }

        try:
            self.authenticate()
            response = self.client.post(url, data)
            self.assert_200(response)
        except Exception:
            import traceback
            logger.warning('\n' + ('*' * 30))
            logger.warning('LEAD WEB INFO EXTRACTION ERROR:')
            logger.warning(traceback.format_exc())
            return

        expected = {
            'project': sample_project.id,
            'date': SAMPLE_WEB_INFO_DATE,
            'country': SAMPLE_WEB_INFO_COUNTRY,
            'website': SAMPLE_WEB_INFO_WEBSITE,
            'title': SAMPLE_WEB_INFO_TITLE,
            'url': SAMPLE_WEB_INFO_URL,
            'source': SAMPLE_WEB_INFO_SOURCE,
            'existing': False,
        }
        self.assertEqual(response.data, expected)
