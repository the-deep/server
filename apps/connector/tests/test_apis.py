from mock import patch

from django.test import override_settings
from deep.tests import TestCase
from user.models import User
from project.models import Project
from organization.models import Organization
from connector.sources.store import get_random_source, acaps_briefing_notes, source_store
from connector.sources.base import OrganizationSearch
from connector.models import (
    Connector,
    ConnectorSource,
    ConnectorUser,
    UnifiedConnector,
    UnifiedConnectorSource,
    # EMMConfig,
)
from connector.sources import store
from .connector_content_mock_data import (
    RELIEF_WEB_MOCK_DATA,
    RELIEF_WEB_MOCK_DATA_LAMBDA_RESPONSE_EXISTING_SOURCES,
    RELIEF_WEB_MOCK_DATA_LAMBDA_RESPONSE_NEW_SOURCES,

    MOCK_CONTENT_DATA_BY_KEY,
    MOCK_LAMBDA_RESPONSE_SOURCES_BY_KEY,
)


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
    #     # TODO Check existing status of leads

    #     connector = self.create(Connector,
    #                             source=get_source_object('rss-feed'),
    #                             params=SAMPLE_RSS_PARAMS,
    #                             role='self')
    #     url = '/api/v1/connectors/{}/leads/'.format(connector.id)

    #     self.authenticate()
    #     response = self.client.post(url)
    #     self.assert_200(response)

    #     self.assertIsNotNone(response.data.get('results'))
    #     self.assertTrue(response.data['count'] >= 0)
    #     self.assertIsInstance(response.data['results'], list)

    # def test_get_leads_from_source(self):
    #     url = '/api/v1/connector-sources/{}/leads/'.format('rss-feed')

    #     self.authenticate()
    #     response = self.client.post(url, data=SAMPLE_RSS_PARAMS)
    #     self.assert_200(response)

    #     self.assertIsNotNone(response.data.get('results'))
    #     self.assertTrue(response.data['count'] > 0)
    #     self.assertIsInstance(response.data['results'], list)

    # def test_get_fields_from_rss(self):
    #     url = '/api/v1/connector-sources/rss-feed/fields/'

    #     self.authenticate()
    #     response = self.client.post(url, data=SAMPLE_RSS_PARAMS)
    #     self.assert_200(response)

    #     self.assertIsNotNone(response.data.get('results'))
    #     self.assertTrue(response.data['count'] > 0)
    #     self.assertIsInstance(response.data['results'], list)

    # def test_relief_web(self):
    #     connector = self.create(Connector,
    #                             source=get_source_object('relief-web'),
    #                             params={'country': 'NPL'},
    #                             role='self')

    #     data = {
    #         'offset': 5,
    #         'limit': 15,
    #         'search': 'Earthquake',
    #     }
    #     url = '/api/v1/connectors/{}/leads/'.format(connector.id)

    #     self.authenticate()
    #     response = self.client.post(url, data=data)
    #     self.assert_200(response)

    #     self.assertIsNotNone(response.data.get('results'))
    #     self.assertTrue(response.data['count'], 15)
    #     self.assertIsInstance(response.data['results'], list)

    #     for result in response.data['results']:
    #         self.assertTrue('earthquake' in result['title'].lower())

    # def test_atom_feed_fields(self):
    #     url = '/api/v1/connector-sources/atom-feed/fields/'

    #     self.authenticate()
    #     response = self.client.post(url, data=SAMPLE_ATOM_PARAMS)
    #     self.assert_200(response)

    # def test_atom_feed_leads(self):
    #     connector = self.create(
    #         Connector,
    #         source=get_source_object(store.atom_feed.AtomFeed.key),
    #         params=SAMPLE_ATOM_PARAMS,
    #         role='self',
    #     )

    #     data = {
    #         'offset': 5,
    #         'limit': 15,
    #     }
    #     url = '/api/v1/connectors/{}/leads/'.format(connector.id)

    #     self.authenticate()
    #     response = self.client.post(url, data=data)
    #     self.assert_200(response)

    #     self.assertIsNotNone(response.data.get('results'))
    #     self.assertTrue(response.data['count'], 15)
    #     self.assertIsInstance(response.data['results'], list)

    # def test_emm_leads(self):
    #     # NOTE: Emm config should have already been created
    #     if not EMMConfig.objects.all().first():
    #         EMMConfig.objects.create()  # Created with default values

    #     connector = self.create(
    #         Connector,
    #         source=get_source_object(store.emm.EMM.key),
    #         params=SAMPLE_EMM_PARAMS,
    #         role='self',
    #     )

    #     data = {
    #         'offset': 5,
    #         'limit': 15,
    #     }
    #     url = '/api/v1/connectors/{}/leads/'.format(connector.id)

    #     self.authenticate()
    #     response = self.client.post(url, data=data)
    #     self.assert_200(response)

    #     self.assertIsNotNone(response.data.get('results'))
    #     self.assertTrue(response.data['count'], 15)
    #     self.assertIsInstance(response.data['results'], list)

    #     for x in response.data['results']:
    #         assert 'emm_entities' in x
    #         assert 'emm_triggers' in x

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

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        response = self.client.get(url)
        self.assert_200(response)
        data = response.data['results']

        for each in data:
            assert 'status' in each
            if each['source'] == 'acaps-briefing-notes':
                assert each['status'] == ConnectorSource.STATUS_BROKEN
            else:
                assert each['status'] == ConnectorSource.STATUS_BROKEN

    def test_organization_search_util(self):
        organization_titles = [
            'Deep',
            'New Deep',
            'Old Deep',
        ]
        Organization.objects.filter(title__in=organization_titles).all().delete()
        assert Organization.objects.filter(title__in=organization_titles).count() == 0

        organization_search = OrganizationSearch(organization_titles)
        organization_search.get('Deep')
        organization_search.get('New Deep')
        organization_search.get('Old Deep')

        assert Organization.objects.filter(title__in=organization_titles).count() == 3


class UnifiedConnectorTest(TestCase):
    sample_unified_connector_data = {
        'clientId': 'random-id-from-client',
        'sources': [
            {
                'params': {
                    'from': '2020-09-10',
                    'country': 'NPL',
                },
                'source': store.relief_web.ReliefWeb.key,
            }
        ],
        'title': 'Nepal Leads',
        'isActive': True,

    }

    def test_unified_connector_common_api(self):
        project = self.create_project()

        url = f'/api/v1/projects/{project.pk}/unified-connectors/'
        data = self.sample_unified_connector_data

        # Test POST API
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)
        data = response.json()
        unified_connector_id = data['id']

        # Test GET API
        url = f'/api/v1/projects/{project.pk}/unified-connectors/{unified_connector_id}/'
        response = self.client.get(url)
        self.assert_200(response)

        # Test PUT API
        data.update({
            'sources': [
                {
                    # Update older connector
                    **data['sources'][0],  # id from here
                    'params': {
                        'from': '2021-09-10',
                        'country': 'NPL',
                    },
                },
                {
                    # Add older connector
                    'params': {
                        'feed-url': 'https://reliefweb.int/country/lby/rss.xml?primary_country=140&created=20180101-20190101',  # noqa: E501
                        'website': 'https://reliefweb.int/',
                        'url-field': 'link',
                        'date-field': 'published',
                        'title-field': 'title',
                    },
                    'source': store.rss_feed.RssFeed.key,
                }
            ],
        })
        url = f'/api/v1/projects/{project.pk}/unified-connectors/{unified_connector_id}/'
        response = self.client.put(url, data)
        response_data = response.json()
        self.assert_200(response)
        self.assertEqual(2, len(response_data['sources']))
        assert data['sources'][0]['id'] in [source['id'] for source in response_data['sources']]

    def test_unified_connector_trigger(self):
        project = self.create_project()

        url = f'/api/v1/projects/{project.pk}/unified-connectors/'
        data = self.sample_unified_connector_data

        # Test POST API
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)
        data = response.json()
        unified_connector_id = data['id']

        # Test process connectors
        url = f'/api/v1/projects/{project.pk}/unified-connectors/{unified_connector_id}/trigger-sync/'
        response = self.client.post(url)
        self.assert_200(response)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('connector.sources.relief_web.requests')
    @patch('connector.tasks.invoke_lambda_function')
    def test_unified_connector_processing(self, invoke_lambda_function_mock, reliefweb_requests_mock):
        project = self.create_project()

        url = f'/api/v1/projects/{project.pk}/unified-connectors/'
        data = self.sample_unified_connector_data

        # Test POST API
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)
        data = response.json()
        unified_connector_id = data['id']
        unified_connector_trigger_url = (
            f'/api/v1/projects/{project.pk}/unified-connectors/{unified_connector_id}/trigger-sync/'
        )
        unified_connector = UnifiedConnector.objects.get(pk=unified_connector_id)

        # Initial lambda error mock #
        # INITIAL MOCK
        reliefweb_requests_mock.post.return_value.text = RELIEF_WEB_MOCK_DATA
        invoke_lambda_function_mock.return_value = [
            500, {'error_message': 'Mock error message'}
        ]
        with self.captureOnCommitCallbacks(execute=True):
            self.assert_200(self.client.post(unified_connector_trigger_url))
        self.assertEqual(
            list(unified_connector.unifiedconnectorsource_set.values_list('status', flat=True)),
            [UnifiedConnectorSource.Status.FAILURE]
        )

        # lambda working mock #
        # Change invoke for mocking lambda responses
        invoke_lambda_function_mock.side_effect = lambda lambda_function, body: [
            # Initial response
            200, {
                'existingSources': RELIEF_WEB_MOCK_DATA_LAMBDA_RESPONSE_EXISTING_SOURCES,
                'asyncJobUuid': 'random-uuid',
            }
        ] if not body.get('asyncJobUuid') else [
            # Pool response (first pending and then success)
            200,
            (
                {'status': 'pending'} if body['retryCount'] == 0 else {
                    'sources': RELIEF_WEB_MOCK_DATA_LAMBDA_RESPONSE_NEW_SOURCES,
                    'status': 'success',
                }
            )
        ]
        with self.captureOnCommitCallbacks(execute=True):
            self.assert_200(self.client.post(unified_connector_trigger_url))
        self.assertEqual(
            list(unified_connector.unifiedconnectorsource_set.values_list('status', flat=True)),
            [UnifiedConnectorSource.Status.SUCCESS]
        )

        # lambda working on first try mock (no pooling required) #
        # Change invoke for mocking lambda responses
        invoke_lambda_function_mock.return_value = [
            200, {
                'existingSources': (
                    RELIEF_WEB_MOCK_DATA_LAMBDA_RESPONSE_EXISTING_SOURCES + RELIEF_WEB_MOCK_DATA_LAMBDA_RESPONSE_NEW_SOURCES
                ),
                'asyncJobUuid': None,
            }
        ]
        with self.captureOnCommitCallbacks(execute=True):
            self.assert_200(self.client.post(unified_connector_trigger_url))
        self.assertEqual(
            list(unified_connector.unifiedconnectorsource_set.values_list('status', flat=True)),
            [UnifiedConnectorSource.Status.SUCCESS]
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('connector.tasks.invoke_lambda_function')
    def test_unified_connector_integration_with_connector(self, invoke_lambda_function_mock):
        project = self.create_project()

        url = f'/api/v1/projects/{project.pk}/unified-connectors/'
        data = {
            'clientId': 'random-id-from-client',
            'sources': [
                {
                    'params': {
                        'from': '2020-09-10',
                        'country': 'NPL',
                    },
                    'source': store.relief_web.ReliefWeb.key,
                }, {
                    'params': {
                        'feed-url': 'https://feedly.com/f/RgQDCHTXsLH8ZTuoy7N2ALOg.atom?count=5',
                        'url-field': 'link',
                        'date-field': 'published',
                        'title-field': 'title',
                        'author-field': None,
                        'source-field': 'author',
                        'website-field': 'link',
                    },
                    'source': store.atom_feed.AtomFeed.key,
                }, {
                    'params': {
                        'feed-url': 'https://reliefweb.int/country/ukr/rss.xml',
                        'url-field': 'link',
                        'date-field': 'author',
                        'title-field': 'title',
                        'source-field': 'source',
                        'website-field': 'link',
                    },
                    'source': store.rss_feed.RssFeed.key,
                }, {
                    'params': {
                        'feed-url': 'https://emm.newsbrief.eu/rss/rss?type=category&id=TH5739-Philippines&duplicates=false',
                        'url-field': 'link',
                        'date-field': 'pubDate',
                        'title-field': 'title',
                        'author-field': 'source',
                        'source-field': 'source',
                        'website-field': 'source',
                    },
                    'source': store.emm.EMM.key,
                },
            ],
            'title': 'Nepal Leads',
            'isActive': True,
        }

        # Test POST API
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)
        data = response.json()
        unified_connector_id = data['id']
        unified_connector_trigger_url = (
            f'/api/v1/projects/{project.pk}/unified-connectors/{unified_connector_id}/trigger-sync/'
        )
        unified_connector = UnifiedConnector.objects.get(pk=unified_connector_id)

        invoke_lambda_function_mock.side_effect = lambda lambda_function, data: [
            200, {
                'existingSources': MOCK_LAMBDA_RESPONSE_SOURCES_BY_KEY[data['source_key']],
                'asyncJobUuid': None,
            }
        ]

        # Start request mock
        mocked_requests = []
        for source_key, _ in source_store.items():
            MOCK_CONTENT_DATA = MOCK_CONTENT_DATA_BY_KEY.get(source_key)
            if not MOCK_CONTENT_DATA:
                continue
            # NOTE: Using __bases__[0] to get the correct class instead of Wrapper Class
            connector_requests_mock = patch(f'{_.__bases__[0].__module__}.requests')
            connector_requests = connector_requests_mock.start()
            for request_method in ['get', 'post']:
                return_value = getattr(connector_requests, request_method).return_value
                return_value.text = return_value.content = return_value.get.return_value = MOCK_CONTENT_DATA
            mocked_requests.append(connector_requests_mock)

        with self.captureOnCommitCallbacks(execute=True):
            self.assert_200(self.client.post(unified_connector_trigger_url))
        self.assertEqual(
            list(unified_connector.unifiedconnectorsource_set.values_list('status', flat=True)),
            [UnifiedConnectorSource.Status.SUCCESS for _ in data['sources']]
        )

        # Stop request mock
        for mocked_request in mocked_requests:
            mocked_request.stop()
