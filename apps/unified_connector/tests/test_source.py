from parameterized import parameterized
from unittest.mock import patch

from utils.graphene.tests import GraphQLTestCase
from project.factories import ProjectFactory

from unified_connector.factories import (
    ConnectorSourceFactory,
    UnifiedConnectorFactory,
)
from unified_connector.models import ConnectorSource
from unified_connector.tests.mock_data.store import ConnectorSourceResponseMock


class TestUnifiedConnectorResponse(GraphQLTestCase):

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        self.uc = UnifiedConnectorFactory.create(project=self.project)

    @staticmethod
    def _assert_lead_equal_to_expected_data(lead_data, expected_data):
        lead_fields = []
        for data in expected_data:
            fields = [str(key) for key, value in data.items()]
            lead_fields += fields
        raw_data = []
        for data in lead_data:
            lead = dict((key, value) for key, value in data.__dict__.items() if key in set(lead_fields))
            raw_data.append(lead)
        assert raw_data == expected_data

    def _connector_response_check(self, source_type, response_mock):
        mock_data = ConnectorSourceResponseMock(source_type)
        response_mock.side_effect = mock_data.get_content_side_effect
        source = ConnectorSourceFactory.create(unified_connector=self.uc, source=source_type, params=mock_data.params)
        leads_result, count = source.source_fetcher().get_leads(source.params)
        self.assertEqual(len(leads_result), len(mock_data.expected_data))
        self.assertEqual(len(leads_result), count)
        self._assert_lead_equal_to_expected_data(leads_result, mock_data.expected_data)

    @parameterized.expand([
        [ConnectorSource.Source.UNHCR, 'unified_connector.sources.unhcr_portal.UNHCRPortal.get_content'],
        [ConnectorSource.Source.RELIEF_WEB, 'unified_connector.sources.relief_web.ReliefWeb.get_content'],
        [ConnectorSource.Source.RSS_FEED, 'unified_connector.sources.rss_feed.RssFeed.get_content'],
        [ConnectorSource.Source.ATOM_FEED, 'unified_connector.sources.atom_feed.AtomFeed.get_content'],
    ])
    def test_connector_source_(self, source_type, response_mock_path):
        response_mock_patch = patch(response_mock_path)
        response_mock = response_mock_patch.start()
        self._connector_response_check(source_type, response_mock)
        response_mock_patch.stop()
