from unittest.mock import patch

from utils.graphene.tests import GraphQLTestCase
from project.factories import ProjectFactory

from unified_connector.factories import (
    ConnectorSourceFactory,
    UnifiedConnectorFactory,
)
from unified_connector.models import ConnectorSource
from unified_connector.tests.mock_data.store import ConnectorSourceResponseMock
from unified_connector.tests.mock_data.rss_feed_mock_data import (
    RSS_FEED_MOCK_DATA_RAW,
    RSS_FEED_MOCK_EXCEPTED_LEADS
)


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
        source = ConnectorSourceFactory.create(unified_connector=self.uc, source=source_type)
        leads_result, count = source.source_fetcher().get_leads(source.params)
        self.assertEqual(len(leads_result), len(mock_data.expected_data))
        self._assert_lead_equal_to_expected_data(leads_result, mock_data.expected_data)

    @patch('unified_connector.sources.unhcr_portal.UNHCRPortal.get_content')
    def test_unhcr_response(self, response_mock):
        return self._connector_response_check(ConnectorSource.Source.UNHCR, response_mock)

    @patch('unified_connector.sources.relief_web.ReliefWeb.get_content')
    def test_relief_web_response(self, response_mock):
        return self._connector_response_check(ConnectorSource.Source.RELIEF_WEB, response_mock)

    @patch('unified_connector.sources.rss_feed.RssFeed.get_content')
    def test_rss_feed_resonse(self, response_mock):
        response_mock.return_value = RSS_FEED_MOCK_DATA_RAW
        source = ConnectorSourceFactory.create(
            unified_connector=self.uc,
            source=ConnectorSource.Source.RSS_FEED,
            params={
                "feed-url": "test-url",
                "url-field": "link",
                "author-field": "author",
                "source-field": "source",
                "date-field": "pubDate",
                "title-field": "title"
            }
        )
        leads_result = source.source_fetcher().get_leads(source.params)
        self._assert_lead_equal_to_expected_data(leads_result[0], RSS_FEED_MOCK_EXCEPTED_LEADS)
