from rest_framework import status
from rest_framework.test import APITestCase
from user.tests import AuthMixin
from user.models import User


class UserTests(AuthMixin, APITestCase):
    def setUp(self):
        self.auth = self.get_auth()

    def test_create_and_update_user(self):
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

    def test_patch_user(self):
        url = '/api/v1/users/{}/'.format(self.user.pk)
        data = {
            'password': 'newpassword',
        }
        response = self.client.patch(url, data,
                                     HTTP_AUTHORIZATION=self.auth,
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
