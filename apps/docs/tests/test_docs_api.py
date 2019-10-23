from rest_framework import status
from rest_framework.test import APITestCase


class DocsApiTests(APITestCase):
    def test_api_success(self):
        url = '/api/v1/docs/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json = response.json()

        self.assertGreaterEqual(len(json['apis']), 1)
        self.assertGreaterEqual(len(json['apis'][0]['endpoints']), 0)
