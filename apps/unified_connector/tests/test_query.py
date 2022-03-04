from utils.graphene.tests import GraphQLTestCase

from unified_connector.models import ConnectorSource

from project.factories import ProjectFactory
from user.factories import UserFactory

from unified_connector.factories import (
    ConnectorLeadFactory,
    ConnectorSourceFactory,
    ConnectorSourceLeadFactory,
    UnifiedConnectorFactory,
)


class TestUnifiedConnectorQuery(GraphQLTestCase):
    ENABLE_NOW_PATCHER = True

    UNIFIED_CONNECTORS_QUERY = '''
        query MyQuery ($id: ID!) {
          project(id: $id) {
            unifiedConnector {
              unifiedConnectors(ordering: ASC_ID) {
                totalCount
                results {
                  id
                  isActive
                  project
                  title
                  leadsCount
                  sources {
                      id
                      params
                      source
                      title
                      unifiedConnector
                      leadsCount
                      stats {
                        date
                        count
                      }
                  }
                }
              }
            }
          }
        }
    '''

    UNIFIED_CONNECTOR_QUERY = '''
        query MyQuery ($id: ID! $connectorId: ID!) {
          project(id: $id) {
            unifiedConnector {
              unifiedConnector(id: $connectorId) {
                id
                isActive
                project
                title
                leadsCount
                sources {
                    id
                    params
                    source
                    title
                    unifiedConnector
                    leadsCount
                    stats {
                      date
                      count
                    }
                }
              }
            }
          }
        }
    '''

    SOURCE_CONNECTORS_QUERY = '''
        query MyQuery ($id: ID!) {
          project(id: $id) {
            unifiedConnector {
              connectorSources(ordering: ASC_ID) {
                totalCount
                results {
                  id
                  params
                  source
                  title
                  unifiedConnector
                  leadsCount
                  stats {
                    date
                    count
                  }
                }
              }
            }
          }
        }
    '''

    SOURCE_CONNECTOR_QUERY = '''
        query MyQuery ($id: ID! $connectorSourceId: ID!) {
          project(id: $id) {
            unifiedConnector {
              connectorSource(id: $connectorSourceId) {
                id
                params
                source
                title
                unifiedConnector
                leadsCount
                stats {
                  date
                  count
                }
              }
            }
          }
        }
    '''

    SOURCE_CONNECTOR_LEADS_QUERY = '''
        query MyQuery ($id: ID!) {
          project(id: $id) {
            unifiedConnector {
              connectorSourceLeads(ordering: ASC_ID) {
                totalCount
                results {
                  id
                  source
                  alreadyAdded
                  blocked
                  connectorLead {
                    id
                    title
                  }
                }
              }
            }
          }
        }
    '''

    SOURCE_CONNECTOR_LEAD_QUERY = '''
        query MyQuery ($id: ID! $connectorSourceLeadId: ID!) {
          project(id: $id) {
            unifiedConnector {
              connectorSourceLead(id: $connectorSourceLeadId) {
                id
                source
                alreadyAdded
                blocked
                connectorLead {
                  id
                  title
                  }
              }
            }
          }
        }
    '''

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        self.user = UserFactory.create()
        self.another_user = UserFactory.create()
        self.project.add_member(self.user)
        self.uc1, self.uc2 = UnifiedConnectorFactory.create_batch(2, project=self.project)
        self.fake_lead = ConnectorLeadFactory.create()
        # NOTE: Some other as noise, making sure they don't conflict with others
        another_project_with_access = ProjectFactory.create()
        another_project_without_access = ProjectFactory.create()
        uc_wc = UnifiedConnectorFactory.create(project=another_project_with_access)
        uc_wtc = UnifiedConnectorFactory.create(project=another_project_without_access)
        uc_wc_source = ConnectorSourceFactory.create(unified_connector=uc_wc, source=ConnectorSource.Source.RELIEF_WEB)
        uc_wtc_source = ConnectorSourceFactory.create(unified_connector=uc_wtc, source=ConnectorSource.Source.RELIEF_WEB)
        ConnectorSourceLeadFactory.create_batch(2, source=uc_wc_source, connector_lead=self.fake_lead)
        ConnectorSourceLeadFactory.create_batch(2, source=uc_wtc_source, connector_lead=self.fake_lead)

    def test_unified_connector_query(self):
        # -- non member user
        self.force_login(self.another_user)
        content = self.query_check(
            self.UNIFIED_CONNECTORS_QUERY, variables=dict(id=self.project.id)
        )['data']['project']['unifiedConnector']
        self.assertEqual(content, None)
        # Single
        content = self.query_check(
            self.UNIFIED_CONNECTOR_QUERY, variables=dict(id=self.project.id, connectorId=str(self.uc1.pk))
        )['data']['project']['unifiedConnector']
        self.assertEqual(content, None)

        # -- member user
        self.force_login(self.user)
        content = self.query_check(
            self.UNIFIED_CONNECTORS_QUERY,
            variables=dict(id=self.project.id),
        )['data']['project']['unifiedConnector']['unifiedConnectors']
        self.assertEqual(content['totalCount'], 2)
        self.assertEqual(content['results'], [
            dict(
                id=str(self.uc1.pk),
                isActive=False,
                project=str(self.project.pk),
                title=self.uc1.title,
                leadsCount=0,
                sources=[],
            ),
            dict(
                id=str(self.uc2.pk),
                isActive=False,
                project=str(self.project.pk),
                title=self.uc2.title,
                leadsCount=0,
                sources=[],
            ),
        ])
        # Single
        content = self.query_check(
            self.UNIFIED_CONNECTOR_QUERY, variables=dict(id=self.project.id, connectorId=str(self.uc1.pk))
        )['data']['project']['unifiedConnector']['unifiedConnector']
        self.assertEqual(
            content, dict(
                id=str(self.uc1.pk),
                isActive=False,
                project=str(self.project.pk),
                title=self.uc1.title,
                leadsCount=0,
                sources=[],
            ),
        )

    def test_connector_source_query(self):
        fake_lead_1 = ConnectorLeadFactory.create(published_on=self.now_datetime.date())
        fake_lead_2 = ConnectorLeadFactory.create(published_on=self.now_datetime.date())
        source1_1 = ConnectorSourceFactory.create(unified_connector=self.uc1, source=ConnectorSource.Source.ATOM_FEED)
        source1_2 = ConnectorSourceFactory.create(unified_connector=self.uc1, source=ConnectorSource.Source.RELIEF_WEB)
        source2_1 = ConnectorSourceFactory.create(unified_connector=self.uc2, source=ConnectorSource.Source.RSS_FEED)
        source2_2 = ConnectorSourceFactory.create(unified_connector=self.uc2, source=ConnectorSource.Source.UNHCR)
        source1_1.leads.add(fake_lead_1)
        source1_1.leads.add(fake_lead_2)
        source2_1.leads.add(fake_lead_2)
        source1_1.generate_stats()
        source2_1.generate_stats()

        # -- non member user
        self.force_login(self.another_user)
        content = self.query_check(
            self.SOURCE_CONNECTORS_QUERY, variables=dict(id=self.project.id)
        )['data']['project']['unifiedConnector']
        self.assertEqual(content, None)
        # Single
        content = self.query_check(
            self.SOURCE_CONNECTOR_QUERY, variables=dict(id=self.project.id, connectorSourceId=str(self.uc1.pk))
        )['data']['project']['unifiedConnector']
        self.assertEqual(content, None)

        ec_source1_1 = dict(
            id=str(source1_1.pk),
            source=self.genum(ConnectorSource.Source.ATOM_FEED),
            title=source1_1.title,
            unifiedConnector=str(self.uc1.pk),
            params={},
            leadsCount=2,
            stats=[{'count': 2, 'date': self.now_datetime.strftime('%Y-%m-%d')}],
        )
        ec_source1_2 = dict(
            id=str(source1_2.pk),
            source=self.genum(ConnectorSource.Source.RELIEF_WEB),
            title=source1_2.title,
            unifiedConnector=str(self.uc1.pk),
            params={},
            leadsCount=0,
            stats=[],
        )
        ec_source2_1 = dict(
            id=str(source2_1.pk),
            source=self.genum(ConnectorSource.Source.RSS_FEED),
            title=source2_1.title,
            unifiedConnector=str(self.uc2.pk),
            params={},
            leadsCount=1,
            stats=[{'count': 1, 'date': self.now_datetime.strftime('%Y-%m-%d')}],
        )
        ec_source2_2 = dict(
            id=str(source2_2.pk),
            source=self.genum(ConnectorSource.Source.UNHCR),
            title=source2_2.title,
            unifiedConnector=str(self.uc2.pk),
            params={},
            leadsCount=0,
            stats=[],
        )

        # -- member user
        self.force_login(self.user)
        content = self.query_check(
            self.SOURCE_CONNECTORS_QUERY,
            variables={'id': self.project.id},
        )['data']['project']['unifiedConnector']['connectorSources']
        self.assertEqual(content['totalCount'], 4)
        self.assertEqual(content['results'], [
            ec_source1_1, ec_source1_2, ec_source2_1, ec_source2_2,
        ])
        # Single
        content = self.query_check(
            self.SOURCE_CONNECTOR_QUERY, variables=dict(id=self.project.id, connectorSourceId=str(source1_2.pk))
        )['data']['project']['unifiedConnector']['connectorSource']
        self.assertEqual(content, ec_source1_2)

        # -- Unified connector -> Sources
        content = self.query_check(
            self.UNIFIED_CONNECTORS_QUERY,
            variables=dict(id=self.project.id),
        )['data']['project']['unifiedConnector']['unifiedConnectors']
        self.assertEqual(content['totalCount'], 2)
        self.assertEqual(content['results'], [
            dict(
                id=str(self.uc1.pk),
                isActive=False,
                project=str(self.project.pk),
                title=self.uc1.title,
                sources=[ec_source1_1, ec_source1_2],
                leadsCount=2,
            ),
            dict(
                id=str(self.uc2.pk),
                isActive=False,
                project=str(self.project.pk),
                title=self.uc2.title,
                sources=[ec_source2_1, ec_source2_2],
                leadsCount=1,
            ),
        ])
        # Single
        content = self.query_check(
            self.UNIFIED_CONNECTOR_QUERY, variables=dict(id=self.project.id, connectorId=str(self.uc1.pk))
        )['data']['project']['unifiedConnector']['unifiedConnector']
        self.assertEqual(
            content, dict(
                id=str(self.uc1.pk),
                isActive=False,
                project=str(self.project.pk),
                title=self.uc1.title,
                sources=[ec_source1_1, ec_source1_2],
                leadsCount=2,
            ),
        )

    def test_connector_source_leads_query(self):
        source1_1 = ConnectorSourceFactory.create(unified_connector=self.uc1, source=ConnectorSource.Source.ATOM_FEED)
        source1_2 = ConnectorSourceFactory.create(unified_connector=self.uc1, source=ConnectorSource.Source.RELIEF_WEB)
        source2_1 = ConnectorSourceFactory.create(unified_connector=self.uc2, source=ConnectorSource.Source.RSS_FEED)
        source2_2 = ConnectorSourceFactory.create(unified_connector=self.uc2, source=ConnectorSource.Source.UNHCR)

        source1_1_leads = ConnectorSourceLeadFactory.create_batch(2, source=source1_1, connector_lead=self.fake_lead)
        source1_2_leads = ConnectorSourceLeadFactory.create_batch(3, source=source1_2, connector_lead=self.fake_lead)
        source2_1_leads = ConnectorSourceLeadFactory.create_batch(4, source=source2_1, connector_lead=self.fake_lead)
        source2_2_leads = ConnectorSourceLeadFactory.create_batch(6, source=source2_2, connector_lead=self.fake_lead)

        self.force_login(self.user)
        content = self.query_check(
            self.SOURCE_CONNECTOR_LEADS_QUERY, variables=dict(id=self.project.id)
        )['data']['project']['unifiedConnector']['connectorSourceLeads']
        self.assertEqual(content['totalCount'], 15)
        self.assertEqual(content['results'], [
            dict(
                id=str(lead.pk),
                alreadyAdded=False,
                blocked=False,
                connectorLead=dict(id=str(self.fake_lead.pk), title=self.fake_lead.title),
                source=str(lead.source_id),
            )
            for lead in [
                *source1_1_leads,
                *source1_2_leads,
                *source2_1_leads,
                *source2_2_leads,
            ]
        ])

        lead = source1_1_leads[0]
        content = self.query_check(
            self.SOURCE_CONNECTOR_LEAD_QUERY, variables=dict(id=self.project.id, connectorSourceLeadId=str(lead.pk))
        )['data']['project']['unifiedConnector']['connectorSourceLead']
        self.assertEqual(
            content, dict(
                id=str(lead.pk),
                alreadyAdded=False,
                blocked=False,
                connectorLead=dict(id=str(self.fake_lead.pk), title=self.fake_lead.title),
                source=str(lead.source_id),
            )
        )
