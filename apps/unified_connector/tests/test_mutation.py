from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from utils.graphene.tests import GraphQLSnapShotTestCase, DUMMY_TEST_CACHES

from project.factories import ProjectFactory
from user.factories import UserFactory

from deep.tests import TestCase
from unified_connector.models import (
    ConnectorLead,
    ConnectorSource,
    ConnectorLeadPreviewImage,
)
from deepl_integration.handlers import UnifiedConnectorLeadHandler
from unified_connector.factories import (
    ConnectorLeadFactory,
    ConnectorSourceFactory,
    ConnectorSourceLeadFactory,
    UnifiedConnectorFactory,
)
from unified_connector.tests.mock_data.relief_web_mock_data import RELIEF_WEB_MOCK_DATA_PAGE_2_RAW


@override_settings(
    CACHES=DUMMY_TEST_CACHES,
)
class TestLeadMutationSchema(GraphQLSnapShotTestCase):
    factories_used = [ProjectFactory, UserFactory, UnifiedConnectorFactory, ConnectorSourceFactory]

    CREATE_UNIFIED_CONNECTOR_MUTATION = '''
        mutation MyMutation ($projectId: ID!  $input: UnifiedConnectorWithSourceInputType!) {
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
        mutation MyMutation ($projectId: ID!  $unifiedConnectorId: ID! $input: UnifiedConnectorWithSourceInputType!) {
          project(id: $projectId) {
            unifiedConnector {
              unifiedConnectorWithSourceUpdate(id: $unifiedConnectorId data: $input) {
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

    UPDATE_CONNECTOR_SOURCE_LEAD_MUTATION = '''
        mutation MyMutation ($projectId: ID!, $connectorSourceLeadId: ID!, $input: ConnectorSourceLeadInputType!) {
          project(id: $projectId) {
            unifiedConnector {
              connectorSourceLeadUpdate(id: $connectorSourceLeadId, data: $input) {
                errors
                ok
                result {
                  id
                  source
                  alreadyAdded
                  blocked
                }
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
        content = _query_check(minput)['data']['project']['unifiedConnector']['unifiedConnectorWithSourceUpdate']['result']
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

    @patch('unified_connector.sources.relief_web.requests')
    @patch('deepl_integration.handlers.requests')
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
                    ConnectorSource.Status.FAILURE,
                    [],
                ),
                (
                    'extractor-invalid',
                    [200, RELIEF_WEB_MOCK_DATA_PAGE_2_RAW],
                    [500, {'error_message': 'Mock error message'}],
                    ConnectorSource.Status.SUCCESS,
                    [ConnectorLead.ExtractionStatus.RETRYING],
                ),
                (
                    'source-invalid',
                    [500, 'invalid-content'],
                    [200, {}],
                    ConnectorSource.Status.FAILURE,
                    [],
                ),
                (
                    'all-good',
                    [200, RELIEF_WEB_MOCK_DATA_PAGE_2_RAW],
                    [200, {}],
                    ConnectorSource.Status.SUCCESS,
                    [ConnectorLead.ExtractionStatus.STARTED],
                ),
        ]:
            reliefweb_requests_mock.post.return_value.status_code = source_response[0]
            reliefweb_requests_mock.post.return_value.text = source_response[1]
            extractor_response_mock.post.return_value.status_code = extractor_response[0]
            extractor_response_mock.post.return_value.text = extractor_response[1]
            with self.captureOnCommitCallbacks(execute=True):
                _query_okay_check()
            self.assertEqual(
                list(uc.sources.values_list('status', flat=True)),
                [expected_source_status.value],
                f'{label}: {expected_source_status.label}'
            )
            self.assertEqual(
                list(connector_lead_qs.distinct().values_list('extraction_status', flat=True)),
                [status.value for status in expected_lead_status],
                f'{label}: {[status.label for status in expected_lead_status]}',
            )
            connector_lead_qs.delete()  # Clear all connector leads

    def test_connector_source_lead_update(self):
        uc = UnifiedConnectorFactory.create(project=self.project)
        fake_lead1 = ConnectorLeadFactory.create()
        source1 = ConnectorSourceFactory.create(
            source=ConnectorSource.Source.ATOM_FEED,
            unified_connector=uc,
        )
        source2 = ConnectorSourceFactory.create(
            source=ConnectorSource.Source.RELIEF_WEB,
            unified_connector=uc,
        )

        connector_source_lead1_1 = ConnectorSourceLeadFactory.create(
            source=source1,
            connector_lead=fake_lead1,
            blocked=False,
        )
        connector_source_lead1_2 = ConnectorSourceLeadFactory.create(
            source=source1,
            connector_lead=fake_lead1,
            blocked=True,
        )

        connector_source_lead2_1 = ConnectorSourceLeadFactory.create(
            source=source2,
            connector_lead=fake_lead1,
            blocked=True,
        )

        def _query_check(minput, source_lead, **kwargs):
            return self.query_check(
                self.UPDATE_CONNECTOR_SOURCE_LEAD_MUTATION,
                minput=minput,
                variables={'projectId': self.project.id, 'connectorSourceLeadId': source_lead.id},
                **kwargs
            )

        minput = dict(blocked=True)

        # -- Without login
        _query_check(minput, connector_source_lead1_1, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(minput, connector_source_lead1_1, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(minput, connector_source_lead1_1, assert_for_error=True)

        # --- member user
        self.force_login(self.member_user)
        for current, source_lead, updated_to in (
            (False, connector_source_lead1_1, True),
            (True, connector_source_lead1_2, False),
            (True, connector_source_lead2_1, True),
        ):
            self.assertEqual(connector_source_lead1_1.blocked, current)
            _query_check(
                dict(blocked=updated_to),
                source_lead,
                mnested=['project', 'unifiedConnector'],
                okay=True,
            )
            source_lead.refresh_from_db()
            self.assertEqual(source_lead.blocked, updated_to)


class UnifiedConnectorCallbackApiTest(TestCase):

    @patch('deepl_integration.handlers.RequestHelper')
    def test_create_connector(self, RequestHelperMock):
        def _check_connector_lead_status(connector_lead, status):
            connector_lead.refresh_from_db()
            self.assertEqual(connector_lead.extraction_status, status)

        url = '/api/v1/callback/unified-connector-lead-extract/'
        connector_lead1 = ConnectorLeadFactory.create(url='https://example.com/some-random-url-01')
        connector_lead2 = ConnectorLeadFactory.create(url='https://example.com/some-random-url-02')

        SAMPLE_SIMPLIFIED_TEXT = 'Sample text'
        RequestHelperMock.return_value.get_text.return_value = SAMPLE_SIMPLIFIED_TEXT
        # Mock file
        file_1 = SimpleUploadedFile(
            name='test_image.jpg', content=b'', content_type='image/jpeg'
        )
        RequestHelperMock.return_value.get_file.return_value = file_1
        # ------ Extraction FAILED
        data = dict(
            client_id='some-random-client-id',
            url='https://example.com/some-random-url',
            images_path=['https://example.com/sample-file-1.jpg'],
            text_path='https://example.com/url-where-data-is-fetched-from-mock-response',
            total_words_count=100,
            total_pages=10,
            extraction_status=0,  # Failed
        )

        response = self.client.post(url, data)
        self.assert_400(response)
        _check_connector_lead_status(connector_lead1, ConnectorLead.ExtractionStatus.PENDING)

        data['client_id'] = UnifiedConnectorLeadHandler.get_client_id(connector_lead1)
        response = self.client.post(url, data)
        self.assert_400(response)
        _check_connector_lead_status(connector_lead1, ConnectorLead.ExtractionStatus.PENDING)

        data['url'] = connector_lead1.url
        response = self.client.post(url, data)
        self.assert_200(response)
        connector_lead1.refresh_from_db()
        _check_connector_lead_status(connector_lead1, ConnectorLead.ExtractionStatus.FAILED)

        # ------ Extraction SUCCESS
        data = dict(
            client_id='some-random-client-id',
            url='https://example.com/some-random-url',
            images_path=['https://example.com/sample-file-1.jpg', 'https://example.com/sample-file-2.jpg'],
            text_path='https://example.com/url-where-data-is-fetched-from-mock-response',
            total_words_count=100,
            total_pages=10,
            extraction_status=1,  # Failed
        )
        response = self.client.post(url, data)
        self.assert_400(response)
        _check_connector_lead_status(connector_lead2, ConnectorLead.ExtractionStatus.PENDING)

        data['client_id'] = UnifiedConnectorLeadHandler.get_client_id(connector_lead2)
        response = self.client.post(url, data)
        self.assert_400(response)
        _check_connector_lead_status(connector_lead2, ConnectorLead.ExtractionStatus.PENDING)

        data['url'] = connector_lead2.url
        response = self.client.post(url, data)
        self.assert_200(response)
        connector_lead2.refresh_from_db()
        _check_connector_lead_status(connector_lead2, ConnectorLead.ExtractionStatus.SUCCESS)
        preview_image_qs = ConnectorLeadPreviewImage.objects.filter(connector_lead=connector_lead2)
        preview_image = preview_image_qs.first()
        self.assertEqual(connector_lead2.simplified_text, SAMPLE_SIMPLIFIED_TEXT)
        self.assertEqual(preview_image_qs.count(), 2)
        self.assertIsNotNone(preview_image and preview_image.image.name)
