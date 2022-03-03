from unittest.mock import patch

from utils.graphene.tests import GraphQLSnapShotTestCase
from unified_connector.models import ConnectorSource

from project.factories import ProjectFactory
from user.factories import UserFactory

from unified_connector.models import ConnectorLead
from unified_connector.factories import (
    # ConnectorLeadFactory,
    # ConnectorSourceLeadFactory,
    ConnectorSourceFactory,
    UnifiedConnectorFactory,
)
from .connector_mock_data import RELIEF_WEB_MOCK_DATA


class TestLeadMutationSchema(GraphQLSnapShotTestCase):
    factories_used = [ProjectFactory, UserFactory, UnifiedConnectorFactory, ConnectorSourceFactory]

    CREATE_UNIFIED_CONNECTOR_MUTATION = '''
        mutation MyMutation ($projectId: ID!  $input: UnifiedConnectorInputType!) {
          project(id: $projectId) {
            unifiedConnector {
              unifiedConnectorCreate(data: $input) {
                ok
                errors
                result {
                  id
                  clientId
                  isActive
                  project
                  title
                  sources {
                    id
                    clientId
                    params
                    source
                    title
                    unifiedConnector
                  }
                }
              }
            }
          }
        }
    '''

    UPDATE_UNIFIED_CONNECTOR_MUTATION = '''
        mutation MyMutation ($projectId: ID!  $unifiedConnectorId: ID! $input: UnifiedConnectorInputType!) {
          project(id: $projectId) {
            unifiedConnector {
              unifiedConnectorUpdate(id: $unifiedConnectorId data: $input) {
                ok
                errors
                result {
                  id
                  clientId
                  isActive
                  project
                  title
                  sources {
                    id
                    clientId
                    params
                    source
                    title
                    unifiedConnector
                  }
                }
              }
            }
          }
        }
    '''

    DELETE_UNIFIED_CONNECTOR_MUTATION = '''
        mutation MyMutation ($projectId: ID!  $unifiedConnectorId: ID!) {
          project(id: $projectId) {
            unifiedConnector {
              unifiedConnectorDelete(id: $unifiedConnectorId) {
                ok
                errors
                result {
                  id
                  clientId
                  isActive
                  project
                  title
                  sources {
                    id
                    clientId
                    params
                    source
                    title
                    unifiedConnector
                  }
                }
              }
            }
          }
        }
    '''

    TRIGGER_UNIFIED_CONNECTOR_MUTATION = '''
        mutation MyMutation ($projectId: ID!  $unifiedConnectorId: ID!) {
          project(id: $projectId) {
            unifiedConnector {
              unifiedConnectorTrigger(id: $unifiedConnectorId) {
                ok
                errors
              }
            }
          }
        }
    '''

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        self.member_user = UserFactory.create()
        self.non_member_user = UserFactory.create()
        self.readonly_member_user = UserFactory.create()
        self.project.add_member(self.member_user)
        self.project.add_member(self.readonly_member_user, role=self.project_role_reader_non_confidential)

    def test_unified_connector_create(self):
        def _query_check(minput, **kwargs):
            return self.query_check(
                self.CREATE_UNIFIED_CONNECTOR_MUTATION,
                minput=minput,
                variables={'projectId': self.project.id},
                **kwargs
            )

        minput = dict(
            title='unified-connector-s-1',
            clientId='u-connector-101',
            isActive=False,
            sources=[
                dict(
                    title='connector-s-1',
                    source=self.genum(ConnectorSource.Source.ATOM_FEED),
                    clientId='connector-source-101',
                    params={
                        'sample-key': 'sample-value',
                    },
                ),
                dict(
                    title='connector-s-2',
                    source=self.genum(ConnectorSource.Source.RELIEF_WEB),
                    clientId='connector-source-102',
                    params={
                        'sample-key': 'sample-value',
                    },
                ),
                dict(
                    title='connector-s-3',
                    # Same as previouse -> Throw error
                    source=self.genum(ConnectorSource.Source.RELIEF_WEB),
                    clientId='connector-source-103',
                    params={
                        'sample-key': 'sample-value',
                    },
                )
            ]
        )

        # -- Without login
        _query_check(minput, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(minput, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(minput, assert_for_error=True)

        # --- member user (with error)
        self.force_login(self.member_user)
        _query_check(minput, okay=False)

        minput['sources'].pop(-1)
        # --- member user
        self.force_login(self.member_user)
        content = _query_check(minput)['data']['project']['unifiedConnector']['unifiedConnectorCreate']['result']
        self.assertMatchSnapshot(content, 'success')

    def test_unified_connector_update(self):
        uc = UnifiedConnectorFactory.create(project=self.project)

        def _query_check(minput, **kwargs):
            return self.query_check(
                self.UPDATE_UNIFIED_CONNECTOR_MUTATION,
                minput=minput,
                variables={'projectId': self.project.id, 'unifiedConnectorId': uc.id},
                **kwargs
            )

        source1 = ConnectorSourceFactory.create(unified_connector=uc, source=ConnectorSource.Source.ATOM_FEED)
        source2 = ConnectorSourceFactory.create(unified_connector=uc, source=ConnectorSource.Source.RELIEF_WEB)
        source3 = ConnectorSourceFactory.create(unified_connector=uc, source=ConnectorSource.Source.RSS_FEED)
        minput = dict(
            clientId='u-connector-101',
            isActive=uc.is_active,
            title=uc.title,
            sources=[
                dict(
                    id=str(source1.pk),
                    clientId='connector-source-101',
                    params=source1.params,
                    source=self.genum(source1.source),
                    title=source1.title,
                ),
                dict(
                    id=str(source2.pk),
                    clientId='connector-source-102',
                    params=source2.params,
                    source=self.genum(source2.source),
                    title=source2.title,
                ),
                dict(
                    # Remove id. This will create a new source
                    clientId='connector-source-103',
                    params=source3.params,
                    source=self.genum(source3.source),
                    title=source3.title,
                ),
                dict(
                    # New source with duplicate source
                    clientId='connector-source-103',
                    params=source1.params,
                    source=self.genum(source1.source),
                    title=source1.title,
                ),
            ]
        )

        # -- Without login
        _query_check(minput, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(minput, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(minput, assert_for_error=True)

        # --- member user (with error)
        self.force_login(self.member_user)
        _query_check(minput, okay=False)

        minput['sources'].pop(-1)
        content = _query_check(minput)['data']['project']['unifiedConnector']['unifiedConnectorUpdate']['result']
        self.assertMatchSnapshot(content, 'success-1')

    def test_unified_connector_delete(self):
        admin_user = UserFactory.create()
        self.project.add_member(admin_user, role=self.project_role_admin)
        uc = UnifiedConnectorFactory.create(project=self.project)

        def _query_check(**kwargs):
            return self.query_check(
                self.DELETE_UNIFIED_CONNECTOR_MUTATION,
                variables={'projectId': self.project.id, 'unifiedConnectorId': uc.id},
                **kwargs
            )

        for source in [ConnectorSource.Source.ATOM_FEED, ConnectorSource.Source.RSS_FEED, ConnectorSource.Source.RELIEF_WEB]:
            ConnectorSourceFactory.create(unified_connector=uc, source=source)
        _query_check(assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(assert_for_error=True)

        # --- member user (error)
        self.force_login(self.member_user)
        _query_check(assert_for_error=True)

        # --- member user
        self.force_login(admin_user)
        _query_check(okay=True, mnested=['project', 'unifiedConnector'])

    @patch('connector.sources.relief_web.requests')
    @patch('lead.tasks.requests')
    def test_unified_connector_trigger(self, extractor_response_mock, reliefweb_requests_mock):
        uc = UnifiedConnectorFactory.create(project=self.project)
        ConnectorSourceFactory.create(unified_connector=uc, source=ConnectorSource.Source.RELIEF_WEB)

        def _query_check(**kwargs):
            return self.query_check(
                self.TRIGGER_UNIFIED_CONNECTOR_MUTATION,
                variables={'projectId': self.project.id, 'unifiedConnectorId': uc.id},
                **kwargs
            )

        def _query_okay_check():
            return _query_check(okay=True, mnested=['project', 'unifiedConnector'])

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(assert_for_error=True)

        # --- member user (inactive)
        self.force_login(self.member_user)
        _query_check(okay=False, mnested=['project', 'unifiedConnector'])

        # --- member user (active)
        uc.is_active = True
        uc.save(update_fields=('is_active',))
        self.force_login(self.member_user)

        connector_lead_qs = ConnectorLead.objects.filter(connectorsourcelead__source__unified_connector=uc)
        for label, source_response, extractor_response, expected_source_status, expected_lead_status in [
                (
                    'both-invalid',
                    [500, 'invalid-content'],
                    [500, {'error_message': 'Mock error message'}],
                    ConnectorSource.Status.FAILURE.value,
                    [],
                ),
                (
                    'extractor-invalid',
                    [200, RELIEF_WEB_MOCK_DATA],
                    [500, {'error_message': 'Mock error message'}],
                    ConnectorSource.Status.SUCCESS.value,
                    [ConnectorLead.ExtractionStatus.RETRYING.value],
                ),
                (
                    'source-invalid',
                    [500, 'invalid-content'],
                    [200, {}],
                    ConnectorSource.Status.FAILURE.value,
                    [],
                ),
                (
                    'all-good',
                    [200, RELIEF_WEB_MOCK_DATA],
                    [200, {}],
                    ConnectorSource.Status.SUCCESS.value,
                    [ConnectorLead.ExtractionStatus.STARTED.value],
                ),
        ]:
            reliefweb_requests_mock.post.return_value.status_code = source_response[0]
            reliefweb_requests_mock.post.return_value.text = source_response[1]
            extractor_response_mock.post.return_value.status_code = extractor_response[0]
            extractor_response_mock.post.return_value.text = extractor_response[1]
            with self.captureOnCommitCallbacks(execute=True):
                _query_okay_check()
            self.assertEqual(
                list(uc.sources.values_list('status', flat=True)), [expected_source_status], label
            )
            self.assertEqual(
                list(connector_lead_qs.distinct().values_list('extraction_status', flat=True)),
                expected_lead_status, label
            )
            connector_lead_qs.delete()  # Clear all connector leads

    """
    def test_unified_connector_integration_with_connector(self):
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

    def test_unified_connector_leads_bulk_action(self):
        project = self.create_project()

        unified_connector_source = self.create(
            UnifiedConnectorSource,
            source=get_source_object(store.atom_feed.AtomFeed.key),
            connector=self.create(UnifiedConnector, project=project),
            blocked=False,
        )
        unified_connector_source_lead1 = self.create(
            UnifiedConnectorSourceLead,
            source=unified_connector_source,
            lead=self.create(ConnectorLead),
            blocked=False,
        )
        unified_connector_source_lead2 = self.create(
            UnifiedConnectorSourceLead,
            source=unified_connector_source,
            lead=self.create(ConnectorLead),
            blocked=True,
        )
        unified_connector_source_lead3 = self.create(
            UnifiedConnectorSourceLead,
            source=unified_connector_source,
            lead=self.create(ConnectorLead),
            blocked=False,
        )

        unified_connector_source2 = self.create(
            UnifiedConnectorSource,
            source=get_source_object(store.atom_feed.AtomFeed.key),
            connector=self.create(UnifiedConnector, project=project),
        )
        unified_connector_source_lead4 = self.create(
            UnifiedConnectorSourceLead,
            source=unified_connector_source2,
            lead=self.create(ConnectorLead),
            blocked=False,
        )

        to_block = [
            unified_connector_source_lead1,
            unified_connector_source_lead3,
            unified_connector_source_lead4,
        ]
        to_unblock = [unified_connector_source_lead2]
        for url in [
            f'/api/v1/projects/{project.id}/unified-connector-sources/{unified_connector_source.id}/leads/bulk-update/',
            f'/api/v1/projects/{project.id}/unified-connectors/{unified_connector_source.connector.id}/leads/bulk-update/',
        ]:
            data = {
                'block': [ele.id for ele in to_block],
                'unblock': [ele.id for ele in to_unblock],
            }

            self.authenticate()
            response = self.client.post(url, data)
            resp_body = response.json()
            self.assert_200(response)
            self.assertEqual(
                sorted([ele.id for ele in to_block if ele.source == unified_connector_source]),
                sorted(resp_body['blocked']),
            )
            self.assertEqual(
                sorted(data['unblock']),
                sorted(resp_body['unblocked']),
            )

            for ele in to_block:
                ele.refresh_from_db()
                self.assertEqual(ele.blocked, ele.source == unified_connector_source)
            for ele in to_unblock:
                ele.refresh_from_db()
                self.assertEqual(ele.blocked, False)
    """
