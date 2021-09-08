from utils.graphene.tests import GraphQLTestCase

from lead.models import Lead

from entry.models import Entry

from user.factories import UserFactory
from project.factories import ProjectFactory
from lead.factories import LeadFactory
from entry.factories import EntryFactory
from analysis_framework.factories import AnalysisFrameworkFactory
from organization.factories import OrganizationFactory, OrganizationTypeFactory


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
                    controlled
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
                        controlled
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
                    controlled
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

    def test_entry_query_filter(self):
        query = '''
            query MyQuery (
                $projectId: ID!
                $authoringOrganizationTypes: [ID]
                $commentStatus: EntryFilterCommentStatusEnum
                $controlled: Boolean
                $createdAt: DateTime
                $createdAt_Gt: DateTime
                $createdAt_Gte: DateTime
                $createdAt_Lt: DateTime
                $createdAt_Lte: DateTime
                $createdBy: [ID]
                $entriesId: [ID]
                $entryTypes: [EntryTagTypeEnum!]
                $excerpt: String
                $filterableData: [EntryFilterDataType!]
                $geoCustomShape: String
                $leadAssignees: [ID]
                $leadConfidentialities: [LeadConfidentialityEnum!]
                $leadGroupLabel: String
                $leadPriorities: [LeadPriorityEnum!]
                $leadPublishedOn: Date
                $leadPublishedOn_Gt: Date
                $leadPublishedOn_Gte: Date
                $leadPublishedOn_Lt: Date
                $leadPublishedOn_Lte: Date
                $leads: [ID]
                $leadStatuses: [LeadStatusEnum!]
                $leadTitle: String
                $modifiedAt: DateTime
                $modifiedBy: [ID]
                $projectEntryLabels: [ID]
            ) {
              project(id: $projectId) {
                entries (
                    commentStatus: $commentStatus
                    controlled: $controlled
                    createdAt: $createdAt
                    createdAt_Gt: $createdAt_Gt
                    createdAt_Gte: $createdAt_Gte
                    createdAt_Lt: $createdAt_Lt
                    createdAt_Lte: $createdAt_Lte
                    createdBy: $createdBy
                    entriesId: $entriesId
                    entryTypes: $entryTypes
                    excerpt: $excerpt
                    filterableData: $filterableData
                    geoCustomShape: $geoCustomShape
                    modifiedAt: $modifiedAt
                    modifiedBy: $modifiedBy
                    projectEntryLabels: $projectEntryLabels
                    # Lead filters
                    authoringOrganizationTypes: $authoringOrganizationTypes
                    leadAssignees: $leadAssignees
                    leadConfidentialities: $leadConfidentialities
                    leadGroupLabel: $leadGroupLabel
                    leadPriorities: $leadPriorities
                    leadPublishedOn: $leadPublishedOn
                    leadPublishedOn_Gt: $leadPublishedOn_Gt
                    leadPublishedOn_Gte: $leadPublishedOn_Gte
                    leadPublishedOn_Lt: $leadPublishedOn_Lt
                    leadPublishedOn_Lte: $leadPublishedOn_Lte
                    leads: $leads
                    leadStatuses: $leadStatuses
                    leadTitle: $leadTitle
                ) {
                  results {
                    id
                  }
                }
              }
            }
        '''

        af = AnalysisFrameworkFactory.create()
        project = ProjectFactory.create(analysis_framework=af)
        org_type1, org_type2 = OrganizationTypeFactory.create_batch(2)
        org1 = OrganizationFactory.create(organization_type=org_type1)
        org2 = OrganizationFactory.create(organization_type=org_type2)
        org3 = OrganizationFactory.create(organization_type=org_type2)
        # User with role
        user = UserFactory.create()
        member1 = UserFactory.create()
        member2 = UserFactory.create()
        project.add_member(user, role=self.project_role_viewer)
        project.add_member(member1, role=self.project_role_viewer)
        project.add_member(member2, role=self.project_role_viewer)
        lead1 = LeadFactory.create(
            project=project,
            title='Test 1',
            source_type=Lead.SourceType.TEXT,
            confidentiality=Lead.Confidentiality.CONFIDENTIAL,
            authors=[org1, org2],
            assignee=[member1],
            priority=Lead.Priority.HIGH,
            status=Lead.Status.PROCESSED,
        )
        lead2 = LeadFactory.create(
            project=project,
            source_type=Lead.SourceType.TEXT,
            title='Test 2',
            assignee=[member2],
            authors=[org2, org3],
            priority=Lead.Priority.HIGH,
        )
        lead3 = LeadFactory.create(
            project=project,
            source_type=Lead.SourceType.WEBSITE,
            url='https://wwwexample.com/sample-1',
            title='Sample 1',
            confidentiality=Lead.Confidentiality.CONFIDENTIAL,
            authors=[org1, org3],
            priority=Lead.Priority.LOW,
        )
        lead4 = LeadFactory.create(
            project=project,
            title='Sample 2',
            authors=[org1],
            priority=Lead.Priority.MEDIUM,
        )

        other_project = ProjectFactory.create(analysis_framework=af)
        other_lead = LeadFactory.create(project=other_project)
        outside_entry = EntryFactory.create(project=other_project, analysis_framework=af, lead=other_lead)
        entry1_1 = EntryFactory.create(
            project=project, analysis_framework=af, lead=lead1, entry_type=Entry.TagType.EXCERPT, controlled=False)
        entry2_1 = EntryFactory.create(
            project=project, analysis_framework=af, lead=lead2, entry_type=Entry.TagType.IMAGE, controlled=True)
        entry3_1 = EntryFactory.create(
            project=project, analysis_framework=af, lead=lead3, entry_type=Entry.TagType.EXCERPT, controlled=False)
        entry4_1 = EntryFactory.create(
            project=project, analysis_framework=af, lead=lead4, entry_type=Entry.TagType.EXCERPT, controlled=False)

        def _query_check(filters, **kwargs):
            return self.query_check(query, variables={'projectId': project.id, **filters}, **kwargs)

        # -- With login
        self.force_login(user)

        # TODO: Add direct test for filter_set as well (is used within export)
        for filter_data, expected_entries in [
            ({'controlled': True}, [entry2_1]),
            ({'controlled': False}, [entry1_1, entry3_1, entry4_1]),
            ({'entriesId': [entry1_1.id, entry2_1.id, outside_entry.id]}, [entry1_1, entry2_1]),
            ({'entryTypes': [self.genum(Entry.TagType.EXCERPT)]}, [entry1_1, entry3_1, entry4_1]),
            (
                {'entryTypes': [self.genum(Entry.TagType.EXCERPT), self.genum(Entry.TagType.IMAGE)]},
                [entry1_1, entry2_1, entry3_1, entry4_1],
            ),
            # TODO: ({'projectEntryLabels': []}, []),
            # TODO: ({'geoCustomShape': []}, []),
            # TODO: After adding comment({'commentStatus': self.genum(EntryFilterMixin.CommentStatus.RESOLVED)}, []),
            # Lead filters
            ({'authoringOrganizationTypes': [org_type2.pk]}, [entry1_1, entry2_1, entry3_1]),
            ({'authoringOrganizationTypes': [org_type1.pk, org_type2.pk]}, [entry1_1, entry2_1, entry3_1, entry4_1]),
            ({'leads': [lead1.pk, lead2.pk]}, [entry1_1, entry2_1]),
            ({'leadTitle': 'test'}, [entry1_1, entry2_1]),
            ({'leadAssignees': [member2.pk]}, [entry2_1]),
            ({'leadAssignees': [member1.pk, member2.pk]}, [entry1_1, entry2_1]),
            ({'leadConfidentialities': self.genum(Lead.Confidentiality.CONFIDENTIAL)}, [entry1_1, entry3_1]),
            ({'leadPriorities': [self.genum(Lead.Priority.HIGH)]}, [entry1_1, entry2_1]),
            (
                {'leadPriorities': [self.genum(Lead.Priority.LOW), self.genum(Lead.Priority.HIGH)]},
                [entry1_1, entry2_1, entry3_1]
            ),
            ({'leadStatuses': [self.genum(Lead.Status.PENDING)]}, [entry2_1, entry3_1, entry4_1]),
            ({'leadStatuses': [self.genum(Lead.Status.PROCESSED), self.genum(Lead.Status.VALIDATED)]}, [entry1_1]),
            # TODO: Common filters
            # ({'excerpt': []}, []),
            # ({'modifiedAt': []}, []),
            # ({'modifiedBy': []}, []),
            # ({'createdAt': []}, []),
            # ({'createdAt_Gt': []}, []),
            # ({'createdAt_Gte': []}, []),
            # ({'createdAt_Lt': []}, []),
            # ({'createdAt_Lte': []}, []),
            # ({'createdBy': []}, []),
            # ({'leadGroupLabel': []}, []),
            # ({'leadPublishedOn': []}, []),
            # ({'leadPublishedOn_Gt': []}, []),
            # ({'leadPublishedOn_Gte': []}, []),
            # ({'leadPublishedOn_Lt': []}, []),
            # ({'leadPublishedOn_Lte': []}, []),
        ]:
            content = _query_check(filter_data)
            self.assertListIds(
                content['data']['project']['entries']['results'], expected_entries,
                {'response': content, 'filter': filter_data}
            )

    # TODO: ({'filterableData': []}, []),
