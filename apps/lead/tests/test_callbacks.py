from rest_framework import status

from deep.tests import TestCase
from project.factories import ProjectFactory
from lead.models import Lead
from lead.factories import LeadFactory
from lead.tasks import LeadExtraction


class TestDeduplicationCallback(TestCase):
    CALLBACK_URL = '/api/v1/callback/lead-deduplication/'

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        self.lead = LeadFactory.create(project=self.project)
        self.client_id = LeadExtraction.generate_lead_client_id(self.lead)

    def test_invalid_params(self):
        invalid_params = [
            ({}, "Empty params"),
            ({"client_id": "abcd"}, "No lead id"),
            ({"lead_id": self.lead.pk, "duplicate_lead_ids": ['abc', '']}, "Invalid duplicate_lead_ids"),
            ({"lead_id": self.lead.pk, "duplicate_lead_ids": []}, "Empty duplicate_lead_ids"),
        ]
        for (post_data, msg) in invalid_params:
            response = self.client.post(self.CALLBACK_URL, data=post_data)
            message = f"{msg} should raise 400"
            self.assert_http_code(response, status.HTTP_400_BAD_REQUEST, message)

    def test_no_client_id(self):
        another_project = ProjectFactory.create()
        # Create 5 leads
        other_leads = [
            LeadFactory.create(project=another_project)
            for _ in range(5)
        ]
        data = {
            "lead_id": self.lead.pk,
            "duplicate_lead_ids": [ld.pk for ld in other_leads],
        }
        response = self.client.post(self.CALLBACK_URL, data=data)
        self.assert_400(response)

    def test_invalid_client_id(self):
        another_project = ProjectFactory.create()
        # Create 5 leads
        other_leads = [
            LeadFactory.create(project=another_project)
            for _ in range(5)
        ]
        data = {
            "lead_id": self.lead.pk,
            "duplicate_lead_ids": [ld.pk for ld in other_leads],
            "client_id": "invalid_client-id",
        }
        response = self.client.post(self.CALLBACK_URL, data=data)
        self.assert_400(response)

    def test_inexistent_lead(self):
        data = {
            "lead_id": 1,
            "duplicate_lead_ids": [],
            "client_id": self.client_id
        }
        response = self.client.post(self.CALLBACK_URL, data=data)
        self.assert_400(response)

    def test_inexistent_duplicate_leads(self):
        data = {
            "lead_id": self.lead.pk,
            "duplicate_lead_ids": [self.lead.pk + x for x in range(1, 4)],
            "client_id": "client_id"
        }
        response = self.client.post(self.CALLBACK_URL, data=data)
        self.assert_400(response)

    def test_duplicate_leads_from_other_projects(self):
        another_project = ProjectFactory.create()
        # Create 5 leads
        other_leads = [
            LeadFactory.create(project=another_project)
            for _ in range(5)
        ]
        data = {
            "lead_id": self.lead.pk,
            "duplicate_lead_ids": [ld.pk for ld in other_leads],
            "client_id": self.client_id,
        }
        response = self.client.post(self.CALLBACK_URL, data=data)
        self.assert_400(response)

    def test_duplicate_leads_callback(self):
        leads = [
            LeadFactory.create(project=self.project)
            for _ in range(5)
        ]
        data = {
            "lead_id": self.lead.pk,
            "duplicate_lead_ids": [ld.pk for ld in leads],
            "client_id": self.client_id,
        }
        response = self.client.post(self.CALLBACK_URL, data=data)
        self.assert_200(response)

        # Check duplicate_leads field of lead
        lead = Lead.objects.get(pk=self.lead.pk)
        assert lead.duplicate_leads is not None
        duplicate_ids = set([x.pk for x in lead.duplicate_leads.all()])
        expected_ids = set([x.pk for x in leads])
        assert duplicate_ids == expected_ids, "Valid duplicate leads should be present"
