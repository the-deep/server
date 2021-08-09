from utils.graphene.tests import GraphQLTestCase

from lead.models import Lead

from user.factories import UserFactory
from project.factories import ProjectFactory
from lead.factories import LeadFactory
from entry.factories import EntryFactory
from analysis_framework.factories import AnalysisFrameworkFactory


class TestEntryQuery(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.af = AnalysisFrameworkFactory.create()
        self.project = ProjectFactory.create(analysis_framework=self.af)
        self.project.add_member(self.user)

    def test_lead_entries_query(self):
        # Includes permissions checks
        query = '''
            query MyQuery ($projectId: ID! $leadId: ID!) {
              project(id: $projectId) {
                lead(id: $leadId) {
                  entries {
                    id
                    order
                    entryType
                    excerpt
                    attributes {
                      widgetType
                      widget
                      data
                      clientId
                      id
                    }
                    clientId
                    droppedExcerpt
                    highlightHidden
                    imageRaw
                    informationDate
                    image {
                      id
                      metadata
                      mimeType
                      title
                      file {
                        url
                        name
                      }
                    }
                    verified
                  }
                }
              }
            }
        '''

        lead = LeadFactory.create(project=self.project)
        entry = EntryFactory.create(project=self.project, analysis_framework=self.af, lead=lead)

        def _query_check(**kwargs):
            return self.query_check(query, variables={'projectId': self.project.pk, 'leadId': lead.id}, **kwargs)

        # Without login
        _query_check(assert_for_error=True)
        # With login
        self.force_login(self.user)
        content = _query_check()
        results = content['data']['project']['lead']['entries']
        self.assertEqual(len(content['data']['project']['lead']['entries']), 1, content)
        self.assertIdEqual(results[0]['id'], entry.pk, results)

    def test_entries_query(self):
        # Includes permissions checks
        query = '''
            query MyQuery ($projectId: ID!) {
              project(id: $projectId) {
                  entries (ordering: "-id") {
                      totalCount
                      results {
                        id
                        order
                        entryType
                        excerpt
                        attributes {
                          widgetType
                          widget
                          data
                          clientId
                          id
                        }
                        clientId
                        droppedExcerpt
                        highlightHidden
                        imageRaw
                        informationDate
                        image {
                          id
                          metadata
                          mimeType
                          title
                          file {
                            url
                            name
                          }
                        }
                        verified
                }
              }
            }
        }
        '''

        user = UserFactory.create()
        lead = LeadFactory.create(project=self.project)
        conf_lead = LeadFactory.create(project=self.project, confidentiality=Lead.Confidentiality.CONFIDENTIAL)
        entry = EntryFactory.create(project=self.project, analysis_framework=self.af, lead=lead)
        conf_entry = EntryFactory.create(project=self.project, analysis_framework=self.af, lead=conf_lead)

        def _query_check(**kwargs):
            return self.query_check(query, variables={'projectId': self.project.pk}, **kwargs)

        # Without login
        _query_check(assert_for_error=True)
        # With login
        self.force_login(user)
        # -- Without membership
        content = _query_check()
        results = content['data']['project']['entries']['results']
        self.assertEqual(content['data']['project']['entries']['totalCount'], 0, content)
        self.assertEqual(len(results), 0, results)
        # -- Without membership (confidential only)
        current_membership = self.project.add_member(user, role=self.project_role_viewer_non_confidential)
        content = _query_check()
        results = content['data']['project']['entries']['results']
        self.assertEqual(content['data']['project']['entries']['totalCount'], 1, content)
        self.assertIdEqual(results[0]['id'], entry.pk, results)
        # -- With membership (non-confidential only)
        current_membership.delete()
        self.project.add_member(user, role=self.project_role_viewer)
        content = _query_check()
        results = content['data']['project']['entries']['results']
        self.assertEqual(content['data']['project']['entries']['totalCount'], 2, content)
        self.assertIdEqual(results[0]['id'], conf_entry.pk, results)
        self.assertIdEqual(results[1]['id'], entry.pk, results)

    def test_entry_query(self):
        # Includes permissions checks
        query = '''
            query MyQuery ($projectId: ID! $entryId: ID!) {
              project(id: $projectId) {
                  entry (id: $entryId) {
                    id
                    order
                    entryType
                    excerpt
                    attributes {
                      widgetType
                      widget
                      data
                      clientId
                      id
                    }
                    clientId
                    droppedExcerpt
                    highlightHidden
                    imageRaw
                    informationDate
                    image {
                      id
                      metadata
                      mimeType
                      title
                      file {
                        url
                        name
                      }
                    }
                    verified
              }
            }
        }
        '''

        user = UserFactory.create()
        lead = LeadFactory.create(project=self.project)
        conf_lead = LeadFactory.create(project=self.project, confidentiality=Lead.Confidentiality.CONFIDENTIAL)
        entry = EntryFactory.create(project=self.project, analysis_framework=self.af, lead=lead)
        conf_entry = EntryFactory.create(project=self.project, analysis_framework=self.af, lead=conf_lead)

        def _query_check(entry, **kwargs):
            return self.query_check(query, variables={'projectId': self.project.pk, 'entryId': entry.id}, **kwargs)

        # Without login
        _query_check(entry, assert_for_error=True)
        _query_check(conf_entry, assert_for_error=True)
        # With login
        self.force_login(user)
        # -- Without membership
        content = _query_check(entry)  # Normal entry
        self.assertEqual(content['data']['project']['entry'], None, content)
        content = _query_check(conf_entry)  # Confidential entry
        self.assertEqual(content['data']['project']['entry'], None, content)
        # -- Without membership (confidential only)
        current_membership = self.project.add_member(user, role=self.project_role_viewer_non_confidential)
        content = _query_check(entry)  # Normal entry
        self.assertNotEqual(content['data']['project']['entry'], None, content)
        content = _query_check(conf_entry)  # Confidential entry
        self.assertEqual(content['data']['project']['entry'], None, content)
        # -- With membership (non-confidential only)
        current_membership.delete()
        self.project.add_member(user, role=self.project_role_viewer)
        content = _query_check(entry)  # Normal entry
        self.assertNotEqual(content['data']['project']['entry'], None, content)
        content = _query_check(conf_entry)  # Confidential entry
        self.assertNotEqual(content['data']['project']['entry'], None, content)
