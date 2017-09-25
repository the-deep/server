from rest_framework.test import APITestCase
from user.tests.test_apis import AuthMixin
from deep.errors import NOT_AUTHENTICATED


class ApiExceptionTests(AuthMixin, APITestCase):
    def setUp(self):
        self.auth = self.get_auth()

    def test_notoken_exception(self):
        url = '/api/v1/users/{}/'.format(self.user.pk)
        data = {
            'password': 'newpassword',
        }
        response = self.client.patch(url, data,
                                     format='json')
        self.assertEqual(response.status_code, 401)
        self.assertIsNotNone(response.data['timestamp'])
        self.assertEqual(response.data['error_code'], NOT_AUTHENTICATED)
