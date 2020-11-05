from mock import patch

from deep.tests import TestCase
from lead.models import Lead, Project, Organization
from lead.tasks import LeadDuplicationInfo


class LeadDuplicationTests(TestCase):
    def setUp(self):
        super().setUp()
        self.author = self.source = self.create_organization()

    def create_organization(self, **kwargs):
        return self.create(Organization, **kwargs)

    @patch('lead.serializers.get_duplicate_leads_in_project_for_source')
    # NOTE that no need to mock add_to_index because that is called only when the get_duplicate_leads
    # return object has attribute 'vector' set. Below we set return value with that attribute defaulting to None
    def test_create_lead_with_duplicate(self, get_duplicate_leads_patch):
        project = self.create(Project, role=self.admin_role)
        lead = self.create(Lead, project=project)
        lead_count = Lead.objects.count()

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

        # If the function(get_duplicate_leads) returns Object with similar_leads attribute, then there are duplicates
        similar_leads = [dict(lead_id=lead.pk, similarity_score=0.9)]
        get_duplicate_leads_patch.return_value = LeadDuplicationInfo(similar_leads=similar_leads)
        # So in this case, we should get 400 error

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_400(response)

        self.assertEqual(Lead.objects.count(), lead_count)

    @patch('lead.serializers.get_duplicate_leads_in_project_for_source')
    # NOTE that no need to mock add_to_index because that is called only when the get_duplicate_leads
    # return object has attribute 'vector' set. Below we set return value with that attribute defaulting to None
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

        get_duplicate_leads_patch.return_value = LeadDuplicationInfo(similar_leads=[])
        # So in this case, where there are no duplicates, we should have 201

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Lead.objects.count(), lead_count + 1)
        r_data = response.json()
        self.assertEqual(r_data['title'], data['title'])
        self.assertEqual(r_data['assignee'], self.user.id)

    @patch('lead.serializers.get_duplicate_leads_in_project_for_source')
    # NOTE that no need to mock add_to_index because that is called only when the get_duplicate_leads
    # return object has attribute 'vector' set. Below we set return value with that attribute defaulting to None
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

        similar_leads = [dict(lead_id=5, similarity_score=0.9)]
        get_duplicate_leads_patch.return_value = LeadDuplicationInfo(similar_leads=similar_leads)
        # So in this case, since we are forcing to save, we should have 201

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Lead.objects.count(), lead_count + 1)
        r_data = response.json()
        self.assertEqual(r_data['title'], data['title'])
        self.assertEqual(r_data['assignee'], self.user.id)
