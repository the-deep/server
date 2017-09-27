from rest_framework import status
from rest_framework.test import APITestCase
from user.tests.test_apis import AuthMixin
from geo.tests.test_apis import RegionMixin
from project.tests.test_apis import ProjectMixin
from project.models import ProjectMembership


class RegionPermissionsTest(AuthMixin, RegionMixin, ProjectMixin,
                            APITestCase):
    """
    Permission tests for geo regions
    """
    def setUp(self):
        self.auth = self.get_auth()

        # One public region
        region = self.create_or_get_region()
        self.region = region

        # One project-private region
        private_region = self.create_or_get_region(public=False)
        project = self.create_or_get_project()
        project.regions.add(private_region)
        self.project = project

        # The url and data used for requests, one for each regon
        self.url = '/api/v1/regions/{}/'.format(region.id)
        self.url2 = '/api/v1/regions/{}/'.format(private_region.id)
        self.data = {
            'title': 'Changed title',
        }

    def get_patch_response(self):
        # Try a patch request for the public region
        response = self.client.patch(self.url, self.data,
                                     HTTP_AUTHORIZATION=self.auth,
                                     format='json')
        return response

    def get_private_patch_response(self):
        # Try a patch request for the private region
        response = self.client.patch(self.url2, self.data,
                                     HTTP_AUTHORIZATION=self.auth,
                                     format='json')
        return response

    def test_404(self):
        """
        Test if a non-project member can see the project private
        region
        """

        ProjectMembership.objects.filter(project=self.project).delete()
        self.assertEqual(self.get_private_patch_response().status_code,
                         status.HTTP_404_NOT_FOUND)

    def test_403(self):
        """
        Test if a non-admin can modify a region

        This involves two tests:
        - Non superuser can modify a public region
        - Non project admin can modify a private region
        """

        self.assertEqual(self.get_patch_response().status_code,
                         status.HTTP_403_FORBIDDEN)

        self.assertEqual(self.get_private_patch_response().status_code,
                         status.HTTP_403_FORBIDDEN)

    def test_admin_level(self):
        """
        Test adding admin level to a region with no permission
        """

        url = '/api/v1/admin-levels/'
        data = {
            'region': self.region.pk,
            'title': 'test',
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)
