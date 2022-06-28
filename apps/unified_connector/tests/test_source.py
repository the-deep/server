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
from unified_connector.sources.base import OrganizationSearch
from organization.models import Organization


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
        leads_result, count = source.source_fetcher().get_leads(source.params, None)
        self.assertEqual(len(leads_result), len(mock_data.expected_data))
        self.assertEqual(len(leads_result), count)
        self._assert_lead_equal_to_expected_data(leads_result, mock_data.expected_data)

    @parameterized.expand([
        [ConnectorSource.Source.UNHCR, 'unified_connector.sources.unhcr_portal.UNHCRPortal.get_content'],
        [ConnectorSource.Source.RELIEF_WEB, 'unified_connector.sources.relief_web.ReliefWeb.get_content'],
        [ConnectorSource.Source.RSS_FEED, 'unified_connector.sources.rss_feed.RssFeed.get_content'],
        [ConnectorSource.Source.ATOM_FEED, 'unified_connector.sources.atom_feed.AtomFeed.get_content'],
        [ConnectorSource.Source.PDNA, 'unified_connector.sources.pdna.PDNA.get_content'],
        [ConnectorSource.Source.HUMANITARIAN_RESP,
            'unified_connector.sources.humanitarian_response.HumanitarianResponse.get_content'],
    ])
    def test_connector_source_(self, source_type, response_mock_path):
        response_mock_patch = patch(response_mock_path)
        response_mock = response_mock_patch.start()
        self._connector_response_check(source_type, response_mock)
        response_mock_patch.stop()

    def test_source_organization(self):
        Organization.objects.create(title='Organization 1', short_name='Organization 1', long_name='Organization 1')
        raw_text_labels = [
            'Organization 1',
            'Relief Web', 'reliefweb', 'the relief web',
        ]
        search_organizaton = OrganizationSearch(raw_text_labels)

        parent_org = Organization.objects.get(title='Relief Web')
        for title in ['reliefweb', 'the relief web']:
            child_org = Organization.objects.get(title__contains=title)
            child_org.parent = parent_org
            child_org.save(update_fields=('parent',))

        for title in ['reliefweb', 'the relief web']:
            self.assertEqual(search_organizaton.get(title), parent_org)

        organization_count1 = Organization.objects.all().count()

        raw_text_labels += [
            'Organization 1', 'the relief web', 'the relief web2'
        ]
        search_organizaton = OrganizationSearch(raw_text_labels)

        child_org = Organization.objects.get(title__contains='the relief web2')
        child_org.parent = parent_org
        child_org.save(update_fields=('parent',))

        organization_count2 = Organization.objects.all().count()

        self.assertEqual(search_organizaton.get('the relief web2'), parent_org)
        self.assertEqual(organization_count1, organization_count2)
