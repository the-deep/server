from rest_framework import status
from rest_framework.test import APITestCase
from user.tests.test_apis import AuthMixin


class JwtApiTests(AuthMixin, APITestCase):
    def setUp(self):
        self.auth = self.get_auth()
        self.test_user = self.create_new_user()

    def test_acces_token(self):
        """
        Test access token

        1. Pass our access token and see if we can
           patch someone's else data. This should fail.
        2. Pass same token and see if we can patch
           our own data. This should succeed.
        """

        data = {
            'password': 'newpassword',
        }
        url = '/api/v1/users/{}/'.format(self.test_user.pk)
        response = self.client.patch(url, data,
                                     HTTP_AUTHORIZATION=self.auth,
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        url = '/api/v1/users/{}/'.format(self.user.pk)
        response = self.client.patch(url, data,
                                     HTTP_AUTHORIZATION=self.auth,
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_refresh_token(self):
        """
        Test refresh token
        """
        data = {
            'refresh': self.refresh,
        }
        url = '/api/v1/token/refresh/'
        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
