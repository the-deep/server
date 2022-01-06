from deep.tests import TestCase
from user.models import User


class JwtApiTests(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_password = 'joHnDave!@#123'

    def test_login_with_password_greater_than_128_characters(self):
        data = {
            'username': "Hari@gmail.com",
            "password": 'abcd' * 130
        }
        url = '/api/v1/token/'

        response = self.client.post(url, data)
        self.assert_400(response)
        assert 'password' in response.data['errors']

    def test_valid_login(self):
        user = User.objects.create_user(username='test@deep.com', password=self.user_password)
        user.is_active = True
        user.save()
        # try to login
        data = {
            'username': user.username,
            'password': self.user_password
        }
        url = '/api/v1/token/'

        # NOTE: Just to make sure empty doesn't throw error
        self.client.credentials(HTTP_AUTHORIZATION='')
        response = self.client.post(url, data=data)
        self.assert_200(response)
        self.assertIn('access', response.data)

    def test_invalid_login_with_password_length_greater_than_128_character(self):
        user = User.objects.create_user(username='test@deep.com', password=self.user_password * 129)
        user.is_active = True
        user.save()
        # try to login
        data = {
            'username': user.username,
            'password': self.user_password * 129
        }
        url = '/api/v1/token/'
        response = self.client.post(url, data=data)
        self.assert_400(response)
        assert 'password' in response.data['errors']
