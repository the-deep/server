from rest_framework import status
from rest_framework.test import APITestCase
from user.tests.test_apis import AuthMixin
from project.tests.test_apis import ProjectMixin
from connector.sources.store import get_random_source
from connector.models import (
    Connector,
    ConnectorUser,
)


class ConnectorMixin():
    def create_or_get_connector(self):
        connector = Connector.objects.first()
        if connector:
            return connector

        connector = Connector.objects.create(
            title='Test connector',
        )

        if self.user:
            ConnectorUser.objects.create(
                user=self.user,
                connector=connector,
                role='admin',
            )

        return connector


class ConnectorApiTest(AuthMixin, ConnectorMixin, ProjectMixin,
                       APITestCase):
    def setUp(self):
        self.auth = self.get_auth()

    def test_create_connector(self):
        url = '/api/v1/connectors/'
        data = {
            'title': 'Test connector',
            'source': get_random_source(),
        }

        last_count = Connector.objects.count()
        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(Connector.objects.count(), last_count + 1)
        self.assertEqual(response.data['title'], data['title'])

        # Test that the user has been made admin
        self.assertEqual(len(response.data['users']), 1)
        self.assertEqual(response.data['users'][0]['user'],
                         self.user.pk)

        user = ConnectorUser.objects.get(
            pk=response.data['users'][0]['id']
        )
        self.assertEqual(user.user.pk, self.user.pk)
        self.assertEqual(user.role, 'admin')

    def test_add_user(self):
        connector = self.create_or_get_connector()
        test_user = self.create_new_user()

        url = '/api/v1/connector-users/'
        data = {
            'user': test_user.pk,
            'connector': connector.pk,
            'role': 'normal',
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], data['role'])
        self.assertEqual(response.data['user'], data['user'])
        self.assertEqual(response.data['connector'], data['connector'])

    def test_add_project(self):
        connector = self.create_or_get_connector()
        test_project = self.create_or_get_project()

        url = '/api/v1/connector-projects/'
        data = {
            'project': test_project.pk,
            'connector': connector.pk,
            'role': 'self',
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], data['role'])
        self.assertEqual(response.data['project'], data['project'])
        self.assertEqual(response.data['connector'], data['connector'])

    def test_list_sources(self):
        url = '/api/v1/connector-sources/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
