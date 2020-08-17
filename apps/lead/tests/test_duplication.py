from mock import patch

from deep.tests import TestCase
from lead.models import Lead, Project, Organization


class LeadDuplicationTests(TestCase):
    def setUp(self):
        super().setUp()
        self.author = self.source = self.create_organization()

    def create_organization(self, **kwargs):
        return self.create(Organization, **kwargs)

    @patch('lead.serializers.get_duplicate_leads')
    def test_create_lead_with_duplicate(self, get_duplicate_leads_patch):
        lead_count = Lead.objects.count()
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': self.source.pk,
            'author': self.author.pk,
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
            'text': 'Alien shapeship has been spotted in the sky',
            'assignee': self.user.id,
        }

        # If the function(get_duplicate_leads) returns (leads_list, None), then there are duplicates
        get_duplicate_leads_patch.return_value = [dict(lead_id=5, similarity_score=0.9)], None
        # So in this case, we should get 400 error

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_400(response)

        self.assertEqual(Lead.objects.count(), lead_count)

    @patch('lead.serializers.get_duplicate_leads')
    def test_create_lead_with_no_duplicate(self, get_duplicate_leads_patch):
        lead_count = Lead.objects.count()
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/leads/'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': self.source.pk,
            'author': self.author.pk,
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
            'text': 'Alien shapeship has been spotted in the sky',
            'assignee': self.user.id,
        }

        # If the function(get_duplicate_leads) returns (leads_list, None), then there are duplicates
        get_duplicate_leads_patch.return_value = [], None
        # So in this case, where there are no duplicates, we should have 201

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Lead.objects.count(), lead_count + 1)
        r_data = response.json()
        self.assertEqual(r_data['title'], data['title'])
        self.assertEqual(r_data['assignee'], self.user.id)

    @patch('lead.serializers.get_duplicate_leads')
    def test_force_create_lead_with_duplicate(self, get_duplicate_leads_patch):
        lead_count = Lead.objects.count()
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/leads/?_force=true'
        data = {
            'title': 'Spaceship spotted in sky',
            'project': project.id,
            'source': self.source.pk,
            'author': self.author.pk,
            'confidentiality': Lead.UNPROTECTED,
            'status': Lead.PENDING,
            'text': 'Alien shapeship has been spotted in the sky',
            'assignee': self.user.id,
        }

        # If the function(get_duplicate_leads) returns (leads_list, None), then there are duplicates
        get_duplicate_leads_patch.return_value = [dict(lead_id=5, similarity_score=0.9)], None
        # So in this case, since we are forcing to save, we should have 201

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Lead.objects.count(), lead_count + 1)
        r_data = response.json()
        self.assertEqual(r_data['title'], data['title'])
        self.assertEqual(r_data['assignee'], self.user.id)
