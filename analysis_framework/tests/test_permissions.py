from rest_framework import status
from rest_framework.test import APITestCase
from user.tests.test_apis import AuthMixin
from analysis_framework.tests.test_apis import AnalysisFrameworkMixin
from project.tests.test_apis import ProjectMixin
from project.models import ProjectMembership


class AnalysisFrameworkPermissionsTest(
        AuthMixin,
        AnalysisFrameworkMixin,
        ProjectMixin,
        APITestCase):
    """
    Permisssion tests for analysis framework api
    """
    def setUp(self):
        self.auth = self.get_auth()

        # Create a project, a entry and a new test user
        analysis_framework = self.create_or_get_analysis_framework()
        test_user = self.create_new_user()
        project = self.create_or_get_project()

        project.analysis_framework = analysis_framework
        project.save()

        # Change admin to new test user
        ProjectMembership.objects.filter(
            project=analysis_framework.project_set.first()
        ).delete()

        ProjectMembership.objects.create(
            project=analysis_framework.project_set.first(),
            member=test_user,
        )

        # The url and data used for requests
        self.url = '/api/v1/entries/{}/'.format(analysis_framework.id)
        self.data = {
            'title': 'Test AnalysisFramework Title',
        }
        self.entry = analysis_framework

    def get_patch_response(self):
        # Try a patch request
        response = self.client.patch(self.url, self.data,
                                     HTTP_AUTHORIZATION=self.auth,
                                     format='json')
        return response

    def test_404(self):
        """
        Test whether a non-project member can access the analysis framework
        """
        self.assertEqual(self.get_patch_response().status_code,
                         status.HTTP_404_NOT_FOUND)

    # There's no need for any more tests since all other cases
    # are successful ones and are auto tested when testing the
    # respective apis.
