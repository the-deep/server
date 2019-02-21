from deep.tests import TestCase
from user.models import User


class JwtApiTests(TestCase):
    def test_access_token(self):
        """
        Test access token

        1. Pass our access token and see if we can
           patch someone's else data. This should fail.
        2. Pass same token and see if we can patch
           our own data. This should succeed.
        """

        test_user = self.create(User)
        data = {
            'password': 'newpassword',
        }
        url = '/api/v1/users/{}/'.format(test_user.pk)

        self.authenticate()
        response = self.client.patch(url, data)
        self.assert_403(response)

        url = '/api/v1/users/{}/'.format(self.user.pk)
        response = self.client.patch(url, data)
        self.assert_200(response)

    def test_refresh_token(self):
        _, refresh = self.authenticate()

        data = {
            'refresh': refresh,
        }
        url = '/api/v1/token/refresh/'

        response = self.client.post(url, data)
        self.assert_200(response)
