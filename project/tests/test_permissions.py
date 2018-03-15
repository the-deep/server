from rest_framework import status
from rest_framework.test import APITestCase
from user.tests.test_apis import AuthMixin
from project.tests.test_apis import ProjectMixin
from project.models import ProjectMembership


class ProjectPermissionsTest(AuthMixin, ProjectMixin, APITestCase):
    """
    Permission tests for project api

    Only failed permission tests are performed here
    as the successful ones are auto tested in the proper
    apis tests.
    """
    def setUp(self):
        self.auth = self.get_auth()

        # Create a project and a new test user
        project = self.create_or_get_project()
        test_user = self.create_new_user()

        # Change admin to new test user
        ProjectMembership.objects.filter(
            project=project
        ).delete()

        ProjectMembership.objects.create(
            project=project,
            member=test_user,
            role='admin',
        )

        # The url and data used for requests
        self.url = '/api/v1/projects/{}/'.format(project.id)
        self.data = {
            'title': 'Changed title',
        }
        self.project = project

    def get_patch_response(self):
        # Try a patch request
        response = self.client.patch(self.url, self.data,
                                     HTTP_AUTHORIZATION=self.auth,
                                     format='json')
        return response

    def test_403(self):
        """
        Test whether a non-admin member can modify the project
        """
        # Now make the user member, but not admin
        # and test again

        ProjectMembership.objects.create(
            project=self.project,
            member=self.user,
            role='normal',
        )

        # We should get 403 error
        self.assertEqual(self.get_patch_response().status_code,
                         status.HTTP_403_FORBIDDEN)
