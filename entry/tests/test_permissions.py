from rest_framework import status
from rest_framework.test import APITestCase
from user.tests.test_apis import AuthMixin
from entry.tests.test_apis import EntryMixin
from lead.tests.test_apis import LeadMixin
from analysis_framework.tests.test_apis import AnalysisFrameworkMixin
from project.tests.test_apis import ProjectMixin
from project.models import ProjectMembership


class EntryPermissionsTest(AuthMixin,
                           EntryMixin,
                           ProjectMixin,
                           LeadMixin,
                           AnalysisFrameworkMixin,
                           APITestCase):
    """
    Permisssion tests for entry api
    """
    def setUp(self):
        self.auth = self.get_auth()

        # Create a project, a entry and a new test user
        entry = self.create_or_get_entry()
        test_user = self.create_new_user()

        # Change admin to new test user
        ProjectMembership.objects.filter(
            project=entry.lead.project
        ).delete()

        ProjectMembership.objects.create(
            project=entry.lead.project,
            member=test_user,
        )

        # The url and data used for requests
        self.url = '/api/v1/entries/{}/'.format(entry.id)
        self.data = {
            'excerpt': 'This is test excerpt',
        }
        self.entry = entry

    def get_patch_response(self):
        # Try a patch request
        response = self.client.patch(self.url, self.data,
                                     HTTP_AUTHORIZATION=self.auth,
                                     format='json')
        return response

    def test_404(self):
        """
        Test whether a non-project member can access the entry
        """
        self.assertEqual(self.get_patch_response().status_code,
                         status.HTTP_404_NOT_FOUND)

    # There's no need for any more tests since all other cases
    # are successful ones and are auto tested when testing the
    # respective apis.
