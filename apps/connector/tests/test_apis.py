from deep.tests import TestCase
from user.models import User
from project.models import Project
from connector.sources.store import get_random_source, acaps_briefing_notes
from connector.models import (
    Connector,
    ConnectorSource,
    ConnectorUser,
    EMMConfig,
)
from connector.sources import store


def get_source_object(key):
    return ConnectorSource.objects.filter(key=key).first()


SAMPLE_RSS_PARAMS = {
    'feed-url': 'https://reliefweb.int/country/afg/rss.xml?primary_country=16',
    'website': 'reliefweb',
    'title-field': 'title',
    'source-field': 'source',
    'author-field': 'author',
    'date-field': 'pubDate',
    'url-field': 'link',
}

SAMPLE_ATOM_PARAMS = {
    'feed-url': 'https://feedly.com/f/Lmh0gtsFqdkr3hzoDFuOeass.atom?count=10',
    'website': 'link',
    'title-field': 'title',
    'source-field': 'author',
    'author-field': 'author',
    'date-field': 'published',
    'url-field': 'link',
}

SAMPLE_EMM_PARAMS = {
    'feed-url': 'https://emm.newsbrief.eu/rss/rss?type=category&'
                'id=filter-FocusedMyanmarEW-Q&language=en&duplicates=false',
    'website-field': 'link',
    'url-field': 'link',
    'date-field': 'pubDate',
    'source-field': 'source',
    'author-field': 'source',
    'title-field': 'title',
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
        connector = self.create(Connector, role='admin')
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
        connector = self.create(Connector, role='admin')
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

    # FIXME: Fix the broken tests by mocking
    # def test_get_leads_from_connector(self):
        # # TODO Check existing status of leads

        # connector = self.create(Connector,
                                # source=get_source_object('rss-feed'),
                                # params=SAMPLE_RSS_PARAMS,
                                # role='self')
        # url = '/api/v1/connectors/{}/leads/'.format(connector.id)

        # self.authenticate()
        # response = self.client.post(url)
        # self.assert_200(response)

        # self.assertIsNotNone(response.data.get('results'))
        # self.assertTrue(response.data['count'] >= 0)
        # self.assertIsInstance(response.data['results'], list)

    # def test_get_leads_from_source(self):
        # url = '/api/v1/connector-sources/{}/leads/'.format('rss-feed')

        # self.authenticate()
        # response = self.client.post(url, data=SAMPLE_RSS_PARAMS)
        # self.assert_200(response)

        # self.assertIsNotNone(response.data.get('results'))
        # self.assertTrue(response.data['count'] > 0)
    #     self.assertIsInstance(response.data['results'], list)

    # def test_get_fields_from_rss(self):
        # url = '/api/v1/connector-sources/rss-feed/fields/'

        # self.authenticate()
        # response = self.client.post(url, data=SAMPLE_RSS_PARAMS)
        # self.assert_200(response)

        # self.assertIsNotNone(response.data.get('results'))
        # self.assertTrue(response.data['count'] > 0)
    #     self.assertIsInstance(response.data['results'], list)

    # def test_relief_web(self):
        # connector = self.create(Connector,
                                # source=get_source_object('relief-web'),
                                # params={'country': 'NPL'},
                                # role='self')

        # data = {
            # 'offset': 5,
            # 'limit': 15,
            # 'search': 'Earthquake',
        # }
        # url = '/api/v1/connectors/{}/leads/'.format(connector.id)

        # self.authenticate()
        # response = self.client.post(url, data=data)
        # self.assert_200(response)

        # self.assertIsNotNone(response.data.get('results'))
        # self.assertTrue(response.data['count'], 15)
        # self.assertIsInstance(response.data['results'], list)

        # for result in response.data['results']:
    #         self.assertTrue('earthquake' in result['title'].lower())

#     def test_atom_feed_fields(self):
        # url = '/api/v1/connector-sources/atom-feed/fields/'

        # self.authenticate()
        # response = self.client.post(url, data=SAMPLE_ATOM_PARAMS)
        # self.assert_200(response)

  #   def test_atom_feed_leads(self):
        # connector = self.create(
            # Connector,
            # source=get_source_object(store.atom_feed.AtomFeed.key),
            # params=SAMPLE_ATOM_PARAMS,
            # role='self',
        # )

        # data = {
            # 'offset': 5,
            # 'limit': 15,
        # }
        # url = '/api/v1/connectors/{}/leads/'.format(connector.id)

        # self.authenticate()
        # response = self.client.post(url, data=data)
        # self.assert_200(response)

        # self.assertIsNotNone(response.data.get('results'))
        # self.assertTrue(response.data['count'], 15)
        # self.assertIsInstance(response.data['results'], list)

    # def test_emm_leads(self):
        # # NOTE: Emm config should have already been created
        # if not EMMConfig.objects.all().first():
            # EMMConfig.objects.create()  # Created with default values

        # connector = self.create(
            # Connector,
            # source=get_source_object(store.emm.EMM.key),
            # params=SAMPLE_EMM_PARAMS,
            # role='self',
        # )

        # data = {
            # 'offset': 5,
            # 'limit': 15,
        # }
        # url = '/api/v1/connectors/{}/leads/'.format(connector.id)

        # self.authenticate()
        # response = self.client.post(url, data=data)
        # self.assert_200(response)

        # self.assertIsNotNone(response.data.get('results'))
        # self.assertTrue(response.data['count'], 15)
        # self.assertIsInstance(response.data['results'], list)

        # for x in response.data['results']:
            # assert 'emm_entities' in x
            # assert 'emm_triggers' in x

    def test_get_connector_fields(self):
        """Check if source and source title are present"""
        connector = self.create(
            Connector,
            source=get_source_object(store.atom_feed.AtomFeed.key),
            params=SAMPLE_ATOM_PARAMS,
            role='self',
        )
        url = '/api/v1/connectors/'

        self.authenticate()
        resp = self.client.get(url)

        self.assert_200(resp)
        data = resp.data['results']
        assert len(data) == 1

        assert data[0]['id'] == connector.id
        assert 'source' in data[0]
        assert 'source_title' in data[0]


class ConnectorSourcesApiTest(TestCase):
    """
    NOTE: The basic connector sources are added from the migration.
    """
    statuses = [ConnectorSource.STATUS_BROKEN, ConnectorSource.STATUS_WORKING]

    def setUp(self):
        super().setUp()
        # Set acaps status working, since might be set broken by other test functions
        acaps_source = ConnectorSource.objects.get(key='acaps-briefing-notes')
        acaps_source.status = ConnectorSource.STATUS_WORKING
        acaps_source.save()

    def test_get_connector_sources_has_status_key(self):
        url = '/api/v1/connector-sources/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        data = response.data['results']
        for each in data:
            assert 'status' in each
            assert each['status'] in self.statuses

    def test_get_connector_acaps_status_broken(self):
        acaps_source = ConnectorSource.objects.get(key='acaps-briefing-notes')
        acaps_source.status = ConnectorSource.STATUS_BROKEN
        acaps_source.save()

        url = '/api/v1/connector-sources/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        data = response.data['results']
        for each in data:
            assert 'status' in each
            if each['key'] == 'acaps-briefing-notes':
                assert each['status'] == ConnectorSource.STATUS_BROKEN
            else:
                assert each['status'] == ConnectorSource.STATUS_WORKING

    def test_get_connectors_have_status_key(self):
        url = '/api/v1/connectors/'
        data = {
            'title': 'Test Acaps connector',
            'source': acaps_briefing_notes.AcapsBriefingNotes.key
        }

        connector_count = Connector.objects.count()

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        response = self.client.get(url)
        self.assert_200(response)
        data = response.data['results']

        for each in data:
            assert 'status' in each
            assert each['status'] in self.statuses

    def test_get_acaps_connector_broken(self):
        acaps_source = ConnectorSource.objects.get(key='acaps-briefing-notes')
        acaps_source.status = ConnectorSource.STATUS_BROKEN
        acaps_source.save()

        url = '/api/v1/connectors/'
        data = {
            'title': 'Test Acaps connector',
            'source': acaps_briefing_notes.AcapsBriefingNotes.key
        }

        connector_count = Connector.objects.count()

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        response = self.client.get(url)
        self.assert_200(response)
        data = response.data['results']

        for each in data:
            print(each)
            assert 'status' in each
            if each['source'] == 'acaps-briefing-notes':
                assert each['status'] == ConnectorSource.STATUS_BROKEN
            else:
                assert each['status'] == ConnectorSource.STATUS_BROKEN
