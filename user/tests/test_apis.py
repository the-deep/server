from rest_framework import status
from rest_framework.test import APITestCase
from user.models import User


class AuthMixin():
    """
    Auth mixin
    Creates users and generates auth token
    """
    def get_auth(self):
        """
        Generates HTTP_AUTHORIZATION
        """
        auth = 'Bearer {0}'.format(self.get_access_token())
        return auth

    def create_new_user(self):
        """
        Create new user.

        Note that often we need multiple test users, so
        this method doesn't look for existing one and always
        return a new one.
        """

        # TODO random username and password
        return User.objects.create_user(
            username='test2@test2.com',
            first_name='Test2',
            last_name='Test2',
            password='admin123',
            email='test2@test2.com',
        )

    def get_access_token(self):
        """
        Create user
        Generate auth token
        """

        # TODO random username and password
        self.user = User.objects.create_user(
            username='test@test.com',
            first_name='Test',
            last_name='Test',
            password='admin123',
            email='test@test.com',
        )
        result = self.client.post(
            '/api/v1/token/',
            data={
                'username': 'test@test.com',
                'password': 'admin123',
            }, format='json')
        return result.data['access']


class UserApiTests(AuthMixin, APITestCase):
    """
    Tests for user apis
    """

    def setUp(self):
        self.auth = self.get_auth()

    def test_create_user(self):
        """
        Post new user
        """
        url = '/api/v1/users/'
        data = {
            'username': 'bibekdahal.bd16@gmail.com',
            'email': 'bibekdahal.bd16@gmail.com',
            'first_name': 'Bibek',
            'last_name': 'Dahal',
            'organization': 'Togglecorp',
            'password': 'admin123',
        }

        # TODO: Test display picture api

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(response.data['username'], data['username'])

        # TODO: Following is a bug of drf, needs to be fixed
        # self.assertEqual(response.data['organization'], data['organization'])

    def test_patch_user(self):
        """
        Change password of existing user

        TODO: Add old_password to change password
        """
        url = '/api/v1/users/{}/'.format(self.user.pk)
        data = {
            'password': 'newpassword',
        }
        response = self.client.patch(url, data,
                                     HTTP_AUTHORIZATION=self.auth,
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_me(self):
        """
        Get self
        """
        url = '/api/v1/users/me/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)
