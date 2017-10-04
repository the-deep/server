from rest_framework import status
from rest_framework.test import APITestCase
from user.tests.test_apis import AuthMixin
from lead.tests.test_apis import LeadMixin
from project.tests.test_apis import ProjectMixin
from project.models import ProjectMembership


class LeadPermissionsTest(AuthMixin, LeadMixin, ProjectMixin,
                          APITestCase):
    """
    Permisssion tests for lead api
    """
    def setUp(self):
        self.auth = self.get_auth()

        # Create a project, a lead and a new test user
        lead = self.create_or_get_lead()
        test_user = self.create_new_user()

        # Change admin to new test user
        ProjectMembership.objects.filter(
            project=lead.project
        ).delete()

        ProjectMembership.objects.create(
            project=lead.project,
            member=test_user,
        )

        # The url and data used for requests
        self.url = '/api/v1/leads/{}/'.format(lead.id)
        self.data = {
            'title': 'Changed title',
        }
        self.lead = lead

    def get_patch_response(self):
        # Try a patch request
        response = self.client.patch(self.url, self.data,
                                     HTTP_AUTHORIZATION=self.auth,
                                     format='json')
        return response

    def test_404(self):
        """
        Test whether a non-project member can access the lead
        """
        self.assertEqual(self.get_patch_response().status_code,
                         status.HTTP_404_NOT_FOUND)

    # There's no need for any more tests since all other cases
    # are successful ones and are auto tested when testing the
    # respective apis.
