from deep.tests import TestCase
from user.models import User
from project.models import Project
from connector.sources.store import get_random_source
from connector.models import (
    Connector,
    ConnectorUser,
)


SAMPLE_RSS_PARAMS = {
    'feed-url': 'https://reliefweb.int/country/afg/rss.xml?primary_country=16',
    'website': 'reliefweb',
    'title-field': 'title',
    'date-field': 'pubDate',
    'url-field': 'link',
}


class ConnectorApiTest(TestCase):
    def test_create_connector(self):
        url = '/api/v1/connectors/'
        data = {
            'title': 'Test connector',
            'source': get_random_source(),
        }

        connector_count = Connector.objects.count()

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Connector.objects.count(), connector_count + 1)
        self.assertEqual(response.data['title'], data['title'])

        # Test that the user has been made admin
        self.assertEqual(len(response.data['users']), 1)
        self.assertEqual(response.data['users'][0]['user'], self.user.pk)

        user = ConnectorUser.objects.get(pk=response.data['users'][0]['id'])
        self.assertEqual(user.user.pk, self.user.pk)
        self.assertEqual(user.role, 'admin')

    def test_add_user(self):
        connector = self.create(Connector)
        test_user = self.create(User)

        url = '/api/v1/connector-users/'
        data = {
            'user': test_user.pk,
            'connector': connector.pk,
            'role': 'normal',
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(response.data['role'], data['role'])
        self.assertEqual(response.data['user'], data['user'])
        self.assertEqual(response.data['connector'], data['connector'])

    def test_add_project(self):
        connector = self.create(Connector)
        test_project = self.create(Project)

        url = '/api/v1/connector-projects/'
        data = {
            'project': test_project.pk,
            'connector': connector.pk,
            'role': 'self',
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(response.data['role'], data['role'])
        self.assertEqual(response.data['project'], data['project'])
        self.assertEqual(response.data['connector'], data['connector'])

    def test_list_sources(self):
        url = '/api/v1/connector-sources/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

    def test_get_leads_from_connector(self):
        # TODO Check existing status of leads

        connector = self.create(Connector,
                                source='rss-feed',
                                params=SAMPLE_RSS_PARAMS)
        url = '/api/v1/connectors/{}/leads/'.format(connector.id)

        self.authenticate()
        response = self.client.post(url)
        self.assert_200(response)

        self.assertIsNotNone(response.data.get('results'))
        self.assertTrue(response.data['count'] >= 0)
        self.assertIsInstance(response.data['results'], list)

    def test_get_leads_from_source(self):
        url = '/api/v1/connector-sources/{}/leads/'.format('rss-feed')

        self.authenticate()
        response = self.client.post(url, data=SAMPLE_RSS_PARAMS)
        self.assert_200(response)

        self.assertIsNotNone(response.data.get('results'))
        self.assertTrue(response.data['count'] > 0)
        self.assertIsInstance(response.data['results'], list)

    def test_get_fields_from_rss(self):
        url = '/api/v1/connector-sources/rss-feed/fields/'

        self.authenticate()
        response = self.client.post(url, data=SAMPLE_RSS_PARAMS)
        self.assert_200(response)

        self.assertIsNotNone(response.data.get('results'))
        self.assertTrue(response.data['count'] > 0)
        self.assertIsInstance(response.data['results'], list)

    def test_relief_web(self):
        connector = self.create(Connector,
                                source='relief-web',
                                params={'country': 'NPL'})

        data = {
            'offset': 5,
            'limit': 15,
            'search': 'Earthquake',
        }
        url = '/api/v1/connectors/{}/leads/'.format(connector.id)

        self.authenticate()
        response = self.client.post(url, data=data)
        self.assert_200(response)

        self.assertIsNotNone(response.data.get('results'))
        self.assertTrue(response.data['count'], 15)
        self.assertIsInstance(response.data['results'], list)

        for result in response.data['results']:
            self.assertTrue('earthquake' in result['title'].lower())
