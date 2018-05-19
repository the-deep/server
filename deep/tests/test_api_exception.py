from deep.tests import TestCase
from deep.errors import NOT_AUTHENTICATED


class ApiExceptionTests(TestCase):
    def test_notoken_exception(self):
        url = '/api/v1/users/{}/'.format(self.user.pk)
        data = {
            'password': 'newpassword',
        }

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 401)
        self.assertIsNotNone(response.data['timestamp'])
        self.assertEqual(response.data['error_code'], NOT_AUTHENTICATED)
