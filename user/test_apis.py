from rest_framework import status
from rest_framework.test import APITestCase
from user.models import User


class UserTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test@test.com',
            first_name='Test',
            last_name='Test',
            password='admin123',
            email='test@test.com',
        )

    def get_access_token(self):
        result = self.client.post(
            '/api/token/',
            data={
                'username': 'test@test.com',
                'password': 'admin123',
            }, format='json')
        return result.data['access']

    def test_create_and_update_user(self):
        url = '/api/users/'
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
        url = '/api/users/{}/'.format(self.user.pk)
        data = {
            'password': 'newpassword',
        }
        auth = 'Bearer {0}'.format(self.get_access_token())
        response = self.client.patch(url, data,
                                     HTTP_AUTHORIZATION=auth,
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
