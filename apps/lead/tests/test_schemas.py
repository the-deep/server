import json

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from utils.graphene.tests import GraphQLTestCase

from organization.factories import OrganizationTypeFactory, OrganizationFactory
from user.factories import UserFactory
from project.factories import ProjectFactory

from lead.models import Lead
from analysis_framework.models import Widget

from entry.factories import EntryFactory
from ary.factories import AssessmentFactory
from geo.factories import (
    RegionFactory,
    GeoAreaFactory,
    AdminLevelFactory,
)
from analysis_framework.factories import (
    AnalysisFrameworkFactory,
    WidgetFactory,
    AfFilterFactory,
)
from lead.factories import (
    LeadEMMTriggerFactory,
    LeadFactory,
    EmmEntityFactory,
    LeadGroupFactory,
    UserSavedLeadFilterFactory,
)

from lead.enums import LeadOrderingEnum


class TestLeadQuerySchema(GraphQLTestCase):
    lead_filter_query = '''
        query MyQuery (
            $projectId: ID!
            # lead Arguments
            $assignees: [ID!]
            $authoringOrganizationTypes: [ID!]
            $authorOrganizations: [ID!]
            $sourceOrganizations: [ID!]
            $confidentiality: LeadConfidentialityEnum
            $createdAt: DateTime
            $createdAtGte: DateTime
            $createdAtLte: DateTime
            $hasEntries: Boolean
            $hasAssessment: Boolean
            $emmEntities: String
            $emmKeywords: String
            $emmRiskFactors: String
            $entriesFilterData: EntriesFilterDataInputType
            $priorities: [LeadPriorityEnum!]
            $publishedOn: Date
            $publishedOnGte: Date
            $publishedOnLte: Date
            $search: String
            $sourceTypes: [LeadSourceTypeEnum!]
            $statuses: [LeadStatusEnum!]
            $text: String
            $url: String
            $ordering: [LeadOrderingEnum!]
            $isAssessment: Boolean
        ) {
          project(id: $projectId) {
            leads (
                assignees: $assignees
                authoringOrganizationTypes: $authoringOrganizationTypes
                authorOrganizations: $authorOrganizations
                sourceOrganizations: $sourceOrganizations
                confidentiality: $confidentiality
                createdAt: $createdAt
                createdAtGte: $createdAtGte
                createdAtLte: $createdAtLte
                hasEntries: $hasEntries
                hasAssessment: $hasAssessment
                emmEntities: $emmEntities
                emmKeywords: $emmKeywords
                emmRiskFactors: $emmRiskFactors
                priorities: $priorities
                publishedOn: $publishedOn
                publishedOnGte: $publishedOnGte
                publishedOnLte: $publishedOnLte
                search: $search
                sourceTypes: $sourceTypes
                statuses: $statuses
                text: $text
                url: $url
                entriesFilterData: $entriesFilterData
                isAssessment: $isAssessment
                ordering: $ordering
            ) {
              results {
                id
              }
            }
          }
        }
    '''

    def test_lead_query(self):
        """
        Test private + non-private project behaviour
        """
        query = '''
            query MyQuery ($projectId: ID! $leadId: ID!) {
              project(id: $projectId) {
                lead (id: $leadId) {
                  id
                  title
                  text
                }
              }
            }
        '''

        project = ProjectFactory.create()
        # User with role
        non_member_user = UserFactory.create()
        member_user = UserFactory.create()
        confidential_member_user = UserFactory.create()
        project.add_member(member_user, role=self.project_role_reader_non_confidential)
        project.add_member(confidential_member_user, role=self.project_role_reader)
        normal_lead = LeadFactory.create(project=project)  # It's UNPROTECTED by default
        confidential_lead = LeadFactory.create(project=project, confidentiality=Lead.Confidentiality.CONFIDENTIAL)

        def _query_check(lead, **kwargs):
            return self.query_check(query, variables={'projectId': project.id, 'leadId': lead.id}, **kwargs)

        # -- Without login
        _query_check(confidential_lead, assert_for_error=True)
        _query_check(normal_lead, assert_for_error=True)

        # -- With login
        self.force_login(non_member_user)

        # --- non-member user
        content = _query_check(normal_lead)
        self.assertEqual(content['data']['project']['lead'], None, content)
        content = _query_check(confidential_lead)
        self.assertEqual(content['data']['project']['lead'], None, content)

        # --- member user
        self.force_login(member_user)
        content = _query_check(normal_lead)
        self.assertNotEqual(content['data']['project']['lead'], None, content)
        content = _query_check(confidential_lead)
        self.assertEqual(content['data']['project']['lead'], None, content)

        # --- confidential member user
        self.force_login(confidential_member_user)
        content = _query_check(normal_lead)
        self.assertNotEqual(content['data']['project']['lead'], None, content)
        content = _query_check(confidential_lead)
        self.assertNotEqual(content['data']['project']['lead'], None, content)

    def test_lead_query_filter(self):
        af = AnalysisFrameworkFactory.create()
        project = ProjectFactory.create(analysis_framework=af)
        org_type1, org_type2 = OrganizationTypeFactory.create_batch(2)
        org1 = OrganizationFactory.create(organization_type=org_type1)
        org2 = OrganizationFactory.create(organization_type=org_type2)
        org3 = OrganizationFactory.create(organization_type=org_type2)
        org1_child = OrganizationFactory.create(organization_type=org_type2, parent=org1)
        # User with role
        user = UserFactory.create()
        member1 = UserFactory.create()
        member2 = UserFactory.create()
        project.add_member(user, role=self.project_role_reader)
        project.add_member(member1, role=self.project_role_reader)
        project.add_member(member2, role=self.project_role_reader)
        lead1 = LeadFactory.create(
            project=project,
            title='Test 1',
            source_type=Lead.SourceType.TEXT,
            confidentiality=Lead.Confidentiality.CONFIDENTIAL,
            source=org1_child,
            authors=[org1, org2],
            assignee=[member1],
            priority=Lead.Priority.HIGH,
            status=Lead.Status.IN_PROGRESS,
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
            source=org2,
            authors=[org1, org3],
            priority=Lead.Priority.LOW,
        )
        lead4 = LeadFactory.create(
            project=project,
            title='Sample 2',
            source=org3,
            authors=[org1],
            priority=Lead.Priority.MEDIUM,
            is_assessment_lead=True,
        )
        lead5 = LeadFactory.create(
            project=project,
            title='Sample 3',
            status=Lead.Status.TAGGED,
            assignee=[member2],
            source=org3,
            is_assessment_lead=True,
        )

        EntryFactory.create(project=project, analysis_framework=af, lead=lead4, controlled=False)
        EntryFactory.create(project=project, analysis_framework=af, lead=lead4, controlled=False)
        EntryFactory.create(project=project, analysis_framework=af, lead=lead5, controlled=True)
        AssessmentFactory.create(project=project, lead=lead1)
        AssessmentFactory.create(project=project, lead=lead2)

        # -- With login
        self.force_login(user)

        # TODO: Add direct test for filter_set as well (is used within export)
        for filter_data, expected_leads in [
            ({'search': 'test'}, [lead1, lead2]),
            ({'confidentiality': self.genum(Lead.Confidentiality.CONFIDENTIAL)}, [lead1, lead3]),
            ({'assignees': [member2.pk]}, [lead2, lead5]),
            ({'assignees': [member1.pk, member2.pk]}, [lead1, lead2, lead5]),
            ({'authoringOrganizationTypes': [org_type2.pk]}, [lead1, lead2, lead3]),
            ({'authoringOrganizationTypes': [org_type1.pk, org_type2.pk]}, [lead1, lead2, lead3, lead4]),
            ({'authorOrganizations': [org1.pk, org2.pk]}, [lead1, lead2, lead3, lead4]),
            ({'authorOrganizations': [org3.pk]}, [lead2, lead3]),
            ({'sourceOrganizations': [org1.pk, org2.pk]}, [lead1, lead3]),
            ({'sourceOrganizations': [org3.pk]}, [lead4, lead5]),
            ({'priorities': [self.genum(Lead.Priority.HIGH)]}, [lead1, lead2]),
            ({'priorities': [self.genum(Lead.Priority.LOW), self.genum(Lead.Priority.HIGH)]}, [lead1, lead2, lead3, lead5]),
            ({'sourceTypes': [self.genum(Lead.SourceType.WEBSITE)]}, [lead3]),
            (
                {'sourceTypes': [self.genum(Lead.SourceType.TEXT), self.genum(Lead.SourceType.WEBSITE)]},
                [lead1, lead2, lead3]
            ),
            ({'statuses': [self.genum(Lead.Status.NOT_TAGGED)]}, [lead2, lead3]),
            ({'statuses': [self.genum(Lead.Status.IN_PROGRESS), self.genum(Lead.Status.TAGGED)]}, [lead1, lead4, lead5]),
            ({'hasEntries': True}, [lead4, lead5]),
            ({'hasEntries': False}, [lead1, lead2, lead3]),
            (
                {
                    'hasEntries': True,
                    'ordering': [self.genum(LeadOrderingEnum.DESC_ENTRIES_COUNT), self.genum(LeadOrderingEnum.ASC_ID)],
                },
                [lead5, lead4]
            ),
            (
                {
                    'hasEntries': True,
                    'entriesFilterData': {},
                    'ordering': [self.genum(LeadOrderingEnum.DESC_ENTRIES_COUNT), self.genum(LeadOrderingEnum.ASC_ID)],
                },
                [lead5, lead4]
            ),
            (
                {
                    'entriesFilterData': {'controlled': True},
                    'ordering': [self.genum(LeadOrderingEnum.DESC_ENTRIES_COUNT), self.genum(LeadOrderingEnum.ASC_ID)],
                },
                [lead5]
            ),
            ({'hasAssessment': True}, [lead1, lead2]),
            ({'hasAssessment': False}, [lead3, lead4, lead5]),
            ({'isAssessment': True}, [lead4, lead5]),
            # TODO:
            # ({'emmEntities': []}, []),
            # ({'emmKeywords': []}, []),
            # ({'emmRiskFactors': []}, []),
            # TODO: Common filters
            # ({'publishedOn': []}, []),
            # ({'publishedOnGte': []}, []),
            # ({'publishedOnLte': []}, []),
            # ({'text': []}, []),
            # ({'url': []}, []),
            # ({'createdAt': []}, []),
            # ({'createdAtGte': []}, []),
            # ({'createdAtLte': []}, []),
        ]:
            content = self.query_check(self.lead_filter_query, variables={'projectId': project.id, **filter_data})
            self.assertListIds(
                content['data']['project']['leads']['results'], expected_leads,
                {'response': content, 'filter': filter_data}
            )

    def test_leads_query(self):
        """
        Test private + non-private project behaviour
        """
        query = '''
            query MyQuery ($id: ID!) {
              project(id: $id) {
                leads {
                  page
                  pageSize
                  totalCount
                  results {
                    id
                    title
                    text
                  }
                }
              }
            }
        '''

        project = ProjectFactory.create()
        # User with role
        non_member_user = UserFactory.create()
        member_user = UserFactory.create()
        confidential_member_user = UserFactory.create()
        project.add_member(member_user, role=self.project_role_reader_non_confidential)
        project.add_member(confidential_member_user, role=self.project_role_reader)
        # Create 10 (5 confidential, 5 non-protected) dummy leads
        normal_leads = LeadFactory.create_batch(5, project=project)  # It's UNPROTECTED by default
        confidential_leads = LeadFactory.create_batch(6, project=project, confidentiality=Lead.Confidentiality.CONFIDENTIAL)

        def _query_check(**kwargs):
            return self.query_check(query, variables={'id': project.id}, **kwargs)

        # -- Without login
        _query_check(assert_for_error=True)

        # -- With login
        self.force_login(non_member_user)

        # --- non-member user (zero leads)
        content = _query_check()

        self.assertEqual(content['data']['project']['leads']['totalCount'], 0, content)
        self.assertEqual(len(content['data']['project']['leads']['results']), 0, content)

        # --- member user (only unprotected leads)
        self.force_login(member_user)
        content = _query_check()
        self.assertEqual(content['data']['project']['leads']['totalCount'], 5, content)
        self.assertListIds(content['data']['project']['leads']['results'], normal_leads, content)

        # --- confidential member user (all leads)
        self.force_login(confidential_member_user)
        content = _query_check()
        self.assertEqual(content['data']['project']['leads']['totalCount'], 11, content)
        self.assertListIds(content['data']['project']['leads']['results'], confidential_leads + normal_leads, content)

    def test_lead_query_with_duplicates_true(self):
        query = '''
            query MyQuery ($projectId: ID!) {
              project(id: $projectId) {
                leads (hasDuplicateLeads: true) {
                  results {
                    id
                    title
                    text
                    duplicateLeadsCount
                  }
                }
              }
            }
        '''
        project = ProjectFactory.create()
        member_user = UserFactory.create()
        project.add_member(member_user, role=self.project_role_reader_non_confidential)
        duplicate_leads = LeadFactory.create_batch(5, project=project)
        lead = LeadFactory.create(project=project)
        lead.duplicate_leads.set(duplicate_leads)
        another_lead = LeadFactory.create(project=project)  # noqa

        """
        NOTE:
        Here, total 7 leads are created: "lead" and 5 duplicates set for lead and
        "another_lead" which has no duplicates nor is assigned to any other lead as duplicate.

        So, while fetching leads with duplicates, there should be 6 leads fetched.
        """

        def _query_check(lead, **kwargs):
            return self.query_check(query, variables={'projectId': project.id}, **kwargs)

        self.force_login(member_user)
        content = _query_check(lead)
        leads_resp = content['data']['project']['leads']['results']
        self.assertEqual(len(leads_resp), 6, "There are 6 leads which have/are duplicates.")

        for lead_resp in leads_resp:
            if lead_resp["id"] == str(lead.id):
                self.assertEqual(lead_resp["duplicateLeadsCount"], 5)
            else:
                self.assertEqual(lead_resp["duplicateLeadsCount"], 1)

    def test_lead_query_with_duplicates_false(self):
        query = '''
            query MyQuery ($projectId: ID!) {
              project(id: $projectId) {
                leads (hasDuplicateLeads: false) {
                    results {
                      id
                      title
                      text
                      duplicateLeadsCount
                    }
                }
              }
            }
        '''
        project = ProjectFactory.create()
        member_user = UserFactory.create()
        project.add_member(member_user, role=self.project_role_reader_non_confidential)
        duplicate_leads = LeadFactory.create_batch(5, project=project)
        lead = LeadFactory.create(project=project)
        lead.duplicate_leads.set(duplicate_leads)
        another_lead = LeadFactory.create(project=project)  # noqa

        def _query_check(lead, **kwargs):
            return self.query_check(query, variables={'projectId': project.id}, **kwargs)

        self.force_login(member_user)
        content = _query_check(lead)
        leads_resp = content['data']['project']['leads']['results']
        self.assertEqual(len(leads_resp), 1)
        lead_resp = leads_resp[0]
        self.assertEqual(lead_resp["id"], str(another_lead.id))
        self.assertEqual(lead_resp["duplicateLeadsCount"], 0)


    def test_lead_query_with_duplicates(self):
        query = '''
            query MyQuery ($projectId: ID! $duplicatesOf: ID!) {
              project(id: $projectId) {
                leads (duplicatesOf: $duplicatesOf) {
                  results {
                    id
                    title
                    entriesCount {
                      total
                      controlled
                    }
                  }
                }
              }
            }
        '''
        project = ProjectFactory.create()
        member_user = UserFactory.create()
        project.add_member(member_user, role=self.project_role_reader_non_confidential)
        duplicate_leads = LeadFactory.create_batch(5, project=project)
        lead = LeadFactory.create(project=project)
        lead.duplicate_leads.set(duplicate_leads)

        def _query_check(lead, **kwargs):
            return self.query_check(query, variables={'projectId': project.id, 'duplicatesOf': lead.id}, **kwargs)

        self.force_login(member_user)
        content = _query_check(lead)
        duplicate_leads_resp = content["data"]["project"]["leads"]["results"]
        self.assertEqual(len(duplicate_leads_resp), len(duplicate_leads))

    def test_lead_query_with_duplicates_reverse(self):
        """
        This tests the following:
        If lead A has duplicate_leads = [B, C, D] then
        querying duplicate leads of either B, C or D should return A.
        """
        query = '''
            query MyQuery ($projectId: ID! $duplicatesOf: ID!) {
              project(id: $projectId) {
                leads (duplicatesOf: $duplicatesOf) {
                  results {
                    id
                    title
                    entriesCount {
                      total
                      controlled
                    }
                  }
                }
              }
            }
        '''
        project = ProjectFactory.create()
        member_user = UserFactory.create()
        project.add_member(member_user, role=self.project_role_reader_non_confidential)
        duplicate_leads = LeadFactory.create_batch(5, project=project)
        lead = LeadFactory.create(project=project)
        lead.duplicate_leads.set(duplicate_leads)

        def _query_check(lead, **kwargs):
            return self.query_check(query, variables={'projectId': project.id, 'duplicatesOf': lead.id}, **kwargs)

        self.force_login(member_user)
        for d_lead in duplicate_leads:
            content = _query_check(d_lead)
            duplicate_leads_resp = content["data"]["project"]["leads"]["results"]
            self.assertEqual(len(duplicate_leads_resp), 1)
            dup = duplicate_leads_resp[0]
            self.assertEqual(dup["id"], str(lead.id))

    def test_leads_fields_query(self):
        """
        Test leads field value
        """
        query = '''
            query MyQuery ($id: ID!) {
              project(id: $id) {
                analysisFramework {
                    id
                }
                leads(ordering: ASC_ID) {
                  page
                  pageSize
                  totalCount
                  results {
                    id
                    status
                    createdAt
                    title
                    publishedOn
                    priority
                    entriesCount {
                      total
                      controlled
                    }
                    authors {
                      id
                      mergedAs {
                        id
                        title
                        logo {
                          id
                          file {
                            name
                            url
                          }
                        }
                      }
                    }
                    source {
                      id
                      logo {
                        id
                        file {
                          name
                          url
                        }
                      }
                      mergedAs {
                        id
                        title
                      }
                    }
                  }
                }
              }
            }
        '''

        af, af_new = AnalysisFrameworkFactory.create_batch(2)
        project = ProjectFactory.create(analysis_framework=af)
        org_type = OrganizationTypeFactory.create()
        org1 = OrganizationFactory.create(organization_type=org_type)
        org2 = OrganizationFactory.create(organization_type=org_type, parent=org1)
        org3 = OrganizationFactory.create(organization_type=org_type)
        # User with role
        user = UserFactory.create()
        project.add_member(user)
        # Create lead
        lead1 = LeadFactory.create(project=project, source=org1)
        lead2 = LeadFactory.create(project=project, source=org2, authors=[org1, org3])
        lead3 = LeadFactory.create(project=project)

        # Some entries for entriesCount
        EntryFactory.create_batch(2, lead=lead1, controlled=True)
        EntryFactory.create_batch(5, lead=lead1)
        EntryFactory.create_batch(10, lead=lead2)

        # -- With login
        self.force_login(user)

        # --- member user (only unprotected leads)
        self.force_login(user)
        content = self.query_check(query, variables={'id': project.id})
        self.assertIdEqual(content['data']['project']['analysisFramework']['id'], af.pk)
        results = content['data']['project']['leads']['results']
        # Count check
        self.assertEqual(content['data']['project']['leads']['totalCount'], 3, content)
        self.assertListIds(results, [lead1, lead2, lead3], content)
        self.assertEqual(len(results[0]['authors']), 0, content)
        # Source check
        self.assertIdEqual(results[0]['source']['id'], org1.id, content)
        self.assertEqual(results[0]['source']['logo']['file']['name'], str(org1.logo.file.name), content)
        self.assertEqual(results[0]['source']['logo']['file']['url'], self.get_media_url(org1.logo.file.name), content)
        # Authors check
        self.assertListIds(results[1]['authors'], [org1, org3], content)
        self.assertIdEqual(results[1]['source']['mergedAs']['id'], org1.id, content)
        # Entries Count check
        for index, (total_count, controlled_count) in enumerate([
            [7, 2],
            [10, 0],
            [0, 0],
        ]):
            self.assertEqual(results[index]['entriesCount']['total'], total_count, content)
            self.assertEqual(results[index]['entriesCount']['controlled'], controlled_count, content)

        # Change AF, this will now not show old entries
        content = self.query_check(query, variables={'id': project.id})
        project.analysis_framework = af_new
        project.save(update_fields=('analysis_framework',))
        EntryFactory.create_batch(2, lead=lead1, controlled=True)
        EntryFactory.create_batch(1, lead=lead2, controlled=False)
        content = self.query_check(query, variables={'id': project.id})
        self.assertIdEqual(content['data']['project']['analysisFramework']['id'], af_new.pk)
        results = content['data']['project']['leads']['results']
        # Entries Count check (After AF change)
        for index, (total_count, controlled_count) in enumerate([
            [2, 2],
            [1, 0],
            [0, 0],
        ]):
            self.assertEqual(results[index]['entriesCount']['total'], total_count, content)
            self.assertEqual(results[index]['entriesCount']['controlled'], controlled_count, content)

    def test_leads_entries_query(self):
        query = '''
            query MyQuery ($id: ID!, $leadId: ID!) {
              project(id: $id) {
                analysisFramework {
                    id
                }
                lead(id: $leadId) {
                    id
                    entriesCount {
                      total
                      controlled
                    }
                    entries {
                        id
                    }
                  }
                }
              }
        '''
        af, af_new = AnalysisFrameworkFactory.create_batch(2)
        user = UserFactory.create()
        project = ProjectFactory.create(analysis_framework=af)
        project.add_member(user, role=self.project_role_member)
        lead = LeadFactory.create(project=project)

        controlled_entries = EntryFactory.create_batch(2, lead=lead, controlled=True)
        not_controlled_entries = EntryFactory.create_batch(3, lead=lead, controlled=False)

        def _query_check():
            return self.query_check(query, variables={'id': project.id, 'leadId': lead.id})

        # -- With login
        self.force_login(user)
        response = _query_check()
        self.assertIdEqual(response['data']['project']['analysisFramework']['id'], af.pk)
        content = response['data']['project']['lead']
        self.assertIdEqual(content['id'], lead.pk, content)
        self.assertEqual(content['entriesCount']['total'], 5, content)
        self.assertEqual(content['entriesCount']['controlled'], 2, content)
        self.assertListIds(content['entries'], [*controlled_entries, *not_controlled_entries], content)

        # Now change AF
        project.analysis_framework = af_new
        project.save(update_fields=('analysis_framework',))

        new_controlled_entries = EntryFactory.create_batch(4, lead=lead, controlled=True)
        new_not_controlled_entries = EntryFactory.create_batch(2, lead=lead, controlled=False)

        response = _query_check()
        self.assertIdEqual(response['data']['project']['analysisFramework']['id'], af_new.pk)
        content = response['data']['project']['lead']
        self.assertIdEqual(content['id'], lead.pk, content)
        self.assertEqual(content['entriesCount']['total'], 6, content)
        self.assertEqual(content['entriesCount']['controlled'], 4, content)
        self.assertListIds(content['entries'], [*new_controlled_entries, *new_not_controlled_entries], content)

    def test_lead_options_query(self):
        """
        Test leads field value
        """
        query = '''
            query MyQuery ($id: ID!) {
              project(id: $id) {
                leadGroups {
                  results {
                    id
                    title
                  }
                  totalCount
                }
                emmEntities {
                  results {
                    id
                    name
                  }
                  totalCount
                }
                leadEmmTriggers {
                  results {
                    count
                    emmKeyword
                    emmRiskFactor
                    id
                  }
                  totalCount
                }
              }
            }
        '''
        project = ProjectFactory.create()
        project2 = ProjectFactory.create()
        member_user = UserFactory.create()
        confidential_member_user = UserFactory.create()
        project.add_member(member_user, role=self.project_role_owner)
        project.add_member(confidential_member_user, role=self.project_role_reader)

        lead_group1 = LeadGroupFactory.create(project=project)
        lead_group2 = LeadGroupFactory.create(project=project)
        LeadGroupFactory.create(project=project2)

        emm_entity_1 = EmmEntityFactory.create()
        emm_entity_2 = EmmEntityFactory.create()
        emm_entity_3 = EmmEntityFactory.create()

        lead1 = LeadFactory.create(
            project=project, emm_entities=[emm_entity_1, emm_entity_2],
            confidentiality=Lead.Confidentiality.CONFIDENTIAL)
        lead2 = LeadFactory.create(project=project, emm_entities=[emm_entity_1])
        lead3 = LeadFactory.create(project=project, emm_entities=[emm_entity_3])
        lead4 = LeadFactory.create(project=project2, emm_entities=[emm_entity_3])

        LeadEMMTriggerFactory.create(lead=lead1)
        LeadEMMTriggerFactory.create(lead=lead2)
        LeadEMMTriggerFactory.create(lead=lead3)
        LeadEMMTriggerFactory.create(lead=lead4)

        self.force_login(member_user)
        # test for lead group
        content = self.query_check(query, variables={'id': project.id})
        self.assertEqual(content['data']['project']['leadGroups']['totalCount'], 2)
        self.assertEqual(
            set(result['id'] for result in content['data']['project']['leadGroups']['results']),
            set([str(lead_group1.id), str(lead_group2.id)])
        )

        # with different project
        content = self.query_check(query, variables={'id': project2.id})
        self.assertEqual(content['data']['project']['leadGroups']['totalCount'], 0)

        # test for emm_entities
        # login with member_user
        content = self.query_check(query, variables={'id': project.id})
        self.assertEqual(content['data']['project']['emmEntities']['totalCount'], 3)

        # login with confidential_member_user
        self.force_login(confidential_member_user)
        content = self.query_check(query, variables={'id': project.id})
        self.assertEqual(content['data']['project']['emmEntities']['totalCount'], 3)

        # test for lead_emm_trigger
        # login with confidential_member_user
        content = self.query_check(query, variables={'id': project.id})
        self.assertEqual(content['data']['project']['leadEmmTriggers']['totalCount'], 3)

        # test for project that user is not member
        content = self.query_check(query, variables={'id': project2.id})
        self.assertEqual(content['data']['project']['leadEmmTriggers']['totalCount'], 0)

    def test_leads_status(self):
        query = '''
            query MyQuery ($id: ID!) {
              project(id: $id) {
                leads(ordering: ASC_ID) {
                  results {
                    id
                    title
                    status
                  }
                }
              }
            }
        '''
        user = UserFactory.create()
        project = ProjectFactory.create(analysis_framework=AnalysisFrameworkFactory.create())
        project.add_member(user)
        lead1, _ = LeadFactory.create_batch(2, project=project)

        def _query_check():
            return self.query_check(query, variables={'id': project.id})

        self.force_login(user)
        content = _query_check()['data']['project']['leads']['results']
        self.assertEqual(len(content), 2, content)
        self.assertEqual(
            set([lead['status'] for lead in content]), {self.genum(Lead.Status.NOT_TAGGED)},
            content,
        )
        # Add entry to lead1
        entry1 = EntryFactory.create(lead=lead1)
        content = _query_check()['data']['project']['leads']['results']
        self.assertEqual(len(content), 2, content)
        self.assertEqual(content[0]['status'], self.genum(Lead.Status.IN_PROGRESS), content)
        self.assertEqual(content[1]['status'], self.genum(Lead.Status.NOT_TAGGED), content)
        # Update lead1 status to TAGGED
        lead1.status = Lead.Status.TAGGED
        lead1.save(update_fields=['status'])
        content = _query_check()['data']['project']['leads']['results']
        self.assertEqual(len(content), 2, content)
        self.assertEqual(content[0]['status'], self.genum(Lead.Status.TAGGED), content)
        self.assertEqual(content[1]['status'], self.genum(Lead.Status.NOT_TAGGED), content)
        # Now update entry1
        entry1.save()
        content = _query_check()['data']['project']['leads']['results']
        self.assertEqual(len(content), 2, content)
        # -- We don't change TAGGED -> IN_PROGRESS
        self.assertEqual(content[0]['status'], self.genum(Lead.Status.TAGGED), content)
        self.assertEqual(content[1]['status'], self.genum(Lead.Status.NOT_TAGGED), content)

    def test_lead_group_query(self):
        query = '''
              query MyQuery ($id: ID!) {
                project(id: $id) {
                  leadGroups(ordering: "id") {
                    results {
                      id
                      title
                      project {
                        id
                      }
                      leadCounts
                    }
                    totalCount
                  }
                }
              }
          '''
        project = ProjectFactory.create()
        project2 = ProjectFactory.create()
        member_user = UserFactory.create()
        non_member_user = UserFactory.create()
        project.add_member(member_user)
        project2.add_member(member_user)

        lead_group1 = LeadGroupFactory.create(project=project)
        lead_group2 = LeadGroupFactory.create(project=project)
        lead_group3 = LeadGroupFactory.create(project=project2)
        LeadFactory.create_batch(4, project=project, lead_group=lead_group1)
        LeadFactory.create_batch(2, project=project, lead_group=lead_group2)
        LeadFactory.create_batch(2, project=project, lead_group=lead_group3)

        self.force_login(member_user)
        content = self.query_check(query, variables={'id': project.id})
        self.assertEqual(content['data']['project']['leadGroups']['totalCount'], 2)
        self.assertEqual(
            set(result['id'] for result in content['data']['project']['leadGroups']['results']),
            set([str(lead_group1.id), str(lead_group2.id)])
        )
        self.assertListIds(content['data']['project']['leadGroups']['results'], [lead_group1, lead_group2], content)

        # login with non_member_user
        self.force_login(non_member_user)
        content = self.query_check(query, variables={'id': project.id})
        self.assertEqual(content['data']['project']['leadGroups']['totalCount'], 0)

        # with different project
        self.force_login(member_user)
        content = self.query_check(query, variables={'id': project2.id})
        self.assertEqual(content['data']['project']['leadGroups']['totalCount'], 1)
        self.assertEqual(content['data']['project']['leadGroups']['results'][0]['id'], str(lead_group3.id))
        self.assertEqual(content['data']['project']['leadGroups']['results'][0]['leadCounts'], 2)

    def test_public_lead_query(self):
        query = '''
            query MyQuery ($uuid: UUID!) {
              publicLead(uuid: $uuid) {
                project {
                  id
                  isRejected
                  membershipPending
                }
                lead {
                  uuid
                  projectTitle
                  url
                  text
                  sourceTypeDisplay
                  sourceType
                  sourceTitle
                  publishedOn
                  createdByDisplayName
                  attachment {
                    title
                    file {
                      url
                      name
                    }
                  }
                }
              }
            }
          '''

        project = ProjectFactory.create()
        # User with role
        non_member_user = UserFactory.create(email='non-member@x.y')
        member_user = UserFactory.create(email='member@x.y')
        confidential_member_user = UserFactory.create(email='confidential-member@x.y')
        project.add_member(member_user, role=self.project_role_reader_non_confidential)
        project.add_member(confidential_member_user, role=self.project_role_reader)
        # Public project
        unprotected_lead = LeadFactory.create(
            project=project,
            confidentiality=Lead.Confidentiality.UNPROTECTED,
            title='unprotected_lead',
        )
        restricted_lead = LeadFactory.create(
            project=project,
            confidentiality=Lead.Confidentiality.RESTRICTED,
            title='restricted_lead',
        )
        confidential_lead = LeadFactory.create(
            project=project,
            confidentiality=Lead.Confidentiality.CONFIDENTIAL,
            title='confidential_lead',
        )

        def _query_check(lead):
            return self.query_check(query, variables={'uuid': str(lead.uuid)})

        cases = [
            # Public Project
            #  is_private, (public_lead, restricted_lead, confidential_lead)
            #   : [Lead, show_project, show_lead, show_project_title]
            (
                False, (False, False, False), [  # Project view public leads
                    (
                        # Without login
                        None, [
                            [unprotected_lead, False, False, None],
                            [restricted_lead, False, False, None],
                            [confidential_lead, False, False, None],
                        ],
                    ),
                    (
                        # Non member user
                        non_member_user, [
                            [unprotected_lead, True, False, None],
                            [restricted_lead, True, False, None],
                            [confidential_lead, True, False, None],
                        ]
                    ),
                    (
                        # Member user with non-confidential access
                        member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, False, None],
                        ]
                    ),
                    (
                        # Member user with confidential access
                        confidential_member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, True, True],
                        ]
                    ),
                ]
            ),
            (
                False, (True, False, False), [  # Project view public leads
                    (
                        # Without login
                        None, [
                            [unprotected_lead, False, True, True],
                            [restricted_lead, False, False, None],
                            [confidential_lead, False, False, None],
                        ],
                    ),
                    (
                        # Non member user
                        non_member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, False, None],
                            [confidential_lead, True, False, None],
                        ]
                    ),
                    (
                        # Member user with non-confidential access
                        member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, False, None],
                        ]
                    ),
                    (
                        # Member user with confidential access
                        confidential_member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, True, True],
                        ]
                    ),
                ]
            ),
            (
                False, (False, True, False), [  # Project view public leads
                    (
                        # Without login
                        None, [
                            [unprotected_lead, False, False, None],
                            [restricted_lead, False, True, True],
                            [confidential_lead, False, False, None],
                        ],
                    ),
                    (
                        # Non member user
                        non_member_user, [
                            [unprotected_lead, True, False, None],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, False, None],
                        ]
                    ),
                    (
                        # Member user with non-confidential access
                        member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, False, None],
                        ]
                    ),
                    (
                        # Member user with confidential access
                        confidential_member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, True, True],
                        ]
                    ),
                ]
            ),
            (
                False, (False, False, True), [  # Project view public leads
                    (
                        # Without login
                        None, [
                            [unprotected_lead, False, False, None],
                            [restricted_lead, False, False, None],
                            [confidential_lead, False, True, True],
                        ],
                    ),
                    (
                        # Non member user
                        non_member_user, [
                            [unprotected_lead, True, False, None],
                            [restricted_lead, True, False, None],
                            [confidential_lead, True, True, True],
                        ]
                    ),
                    (
                        # Member user with non-confidential access
                        member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, True, True],
                        ]
                    ),
                    (
                        # Member user with confidential access
                        confidential_member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, True, True],
                        ]
                    ),
                ]
            ),
            # Private Project
            (
                True, (False, False, False), [  # Project view public leads
                    (
                        # Without login
                        None, [
                            [unprotected_lead, False, False, None],
                            [restricted_lead, False, False, None],
                            [confidential_lead, False, False, None],
                        ],
                    ),
                    (
                        # Non member user
                        non_member_user, [
                            [unprotected_lead, False, False, None],
                            [restricted_lead, False, False, None],
                            [confidential_lead, False, False, None],
                        ]
                    ),
                    (
                        # Member user with non-confidential access
                        member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, False, None],
                        ]
                    ),
                    (
                        # Member user with confidential access
                        confidential_member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, True, True],
                        ]
                    ),
                ]
            ),
            (
                True, (True, False, False), [  # Project view public leads
                    (
                        # Without login
                        None, [
                            [unprotected_lead, False, True, False],
                            [restricted_lead, False, False, None],
                            [confidential_lead, False, False, None],
                        ],
                    ),
                    (
                        # Non member user
                        non_member_user, [
                            [unprotected_lead, False, True, False],
                            [restricted_lead, False, False, None],
                            [confidential_lead, False, False, None],
                        ]
                    ),
                    (
                        # Member user with non-confidential access
                        member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, False, None],
                        ]
                    ),
                    (
                        # Member user with confidential access
                        confidential_member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, True, True],
                        ]
                    ),
                ]
            ),
            (
                True, (False, True, False), [  # Project view public leads
                    (
                        # Without login
                        None, [
                            [unprotected_lead, False, False, None],
                            [restricted_lead, False, True, False],
                            [confidential_lead, False, False, None],
                        ],
                    ),
                    (
                        # Non member user
                        non_member_user, [
                            [unprotected_lead, False, False, None],
                            [restricted_lead, False, True, False],
                            [confidential_lead, False, False, None],
                        ]
                    ),
                    (
                        # Member user with non-confidential access
                        member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, False, None],
                        ]
                    ),
                    (
                        # Member user with confidential access
                        confidential_member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, True, True],
                        ]
                    ),
                ]
            ),
            (
                True, (False, False, True), [  # Project view public leads
                    (
                        # Without login
                        None, [
                            [unprotected_lead, False, False, None],
                            [restricted_lead, False, False, None],
                            [confidential_lead, False, True, False],
                        ],
                    ),
                    (
                        # Non member user
                        non_member_user, [
                            [unprotected_lead, False, False, None],
                            [restricted_lead, False, False, None],
                            [confidential_lead, False, True, False],
                        ]
                    ),
                    (
                        # Member user with non-confidential access
                        member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, True, True],
                        ]
                    ),
                    (
                        # Member user with confidential access
                        confidential_member_user, [
                            [unprotected_lead, True, True, True],
                            [restricted_lead, True, True, True],
                            [confidential_lead, True, True, True],
                        ]
                    ),
                ]
            ),
        ]

        for (
            is_private,
            (
                project_show_public_leads,
                project_show_restricted_leads,
                project_show_confidential_leads,
            ),
            user_and_conditions,
        ) in cases:
            project.is_private = is_private
            project.has_publicly_viewable_unprotected_leads = project_show_public_leads
            project.has_publicly_viewable_restricted_leads = project_show_restricted_leads
            project.has_publicly_viewable_confidential_leads = project_show_confidential_leads
            project.save(
                update_fields=(
                    'is_private',
                    'has_publicly_viewable_unprotected_leads',
                    'has_publicly_viewable_restricted_leads',
                    'has_publicly_viewable_confidential_leads',
                )
            )
            for user, conditions in user_and_conditions:
                if user:
                    self.force_login(user)
                else:
                    self.logout()
                for used_lead, expect_project_membership_data, expect_lead, show_project_title in conditions:
                    content = _query_check(used_lead)['data']['publicLead']
                    check_meta = dict(
                        project_private=is_private,
                        project_show=dict(
                            public_leads=project_show_public_leads,
                            restricted_leads=project_show_restricted_leads,
                            confidential_leads=project_show_confidential_leads,
                        ),
                        user=user,
                        used_lead=used_lead,
                    )
                    # Excepted Lead
                    if expect_lead:
                        self.assertIsNotNone(content['lead'], check_meta)
                        self.assertEqual(content['lead']['uuid'], str(used_lead.uuid))
                        # Show project title in Lead data.
                        if show_project_title:
                            self.assertIsNotNone(content['lead']['projectTitle'], check_meta)
                        else:
                            self.assertIsNone(content['lead']['projectTitle'], check_meta)
                    else:
                        self.assertIsNone(content['lead'], check_meta)
                    # Show project with membership data
                    if expect_project_membership_data:
                        self.assertIsNotNone(content['project'], check_meta)
                        self.assertEqual(content['project']['id'], str(used_lead.project_id))
                    else:
                        self.assertIsNone(content['project'], check_meta)


class TestUserSavedLeadFilters(GraphQLTestCase):
    LEAD_FILTER_SAVE_QUERY = '''
        query MyQuery ($id: ID!) {
          project(id: $id) {
            userSavedLeadFilter {
              id
              title
              filters {
                assignees
                authorOrganizations
                authoringOrganizationTypes
                createdBy
                modifiedBy
                sourceOrganizations
                entriesFilterData {
                    createdBy
                    leadAssignees
                    leadAuthorOrganizations
                    leadAuthoringOrganizationTypes
                    leadCreatedBy
                    leadSourceOrganizations
                    modifiedBy
                }
              }
              filtersData {
                assigneeOptions { id }
                authorOrganizationOptions { id }
                authorOrganizationTypeOptions { id }
                createdByOptions { id }
                modifiedByOptions { id }
                entryFilterCreatedByOptions { id }
                entryFilterGeoAreaOptions { id }
                entryFilterLeadAssigneeOptions { id }
                entryFilterLeadAuthorOrganizationOptions { id }
                entryFilterLeadAuthoringOrganizationTypeOptions { id }
                entryFilterLeadCreatedByOptions { id }
                entryFilterLeadSourceOrganizationOptions { id }
                entryFilterModifiedByOptions { id }
                sourceOrganizationOptions { id }
              }
            }
          }
        }
    '''

    LEAD_FILTER_SAVE_MUTATION = '''
        mutation MyMutation ($id: ID!, $input: UserSavedLeadFilterInputType!) {
          project(id: $id) {
            leadFilterSave(data: $input) {
              ok
              errors
              result {
                id
                title
                filters {
                    ids
                }
                filtersData {
                  assigneeOptions { id }
                  authorOrganizationOptions { id }
                  authorOrganizationTypeOptions { id }
                  createdByOptions { id }
                  modifiedByOptions { id }
                  entryFilterCreatedByOptions { id }
                  entryFilterGeoAreaOptions { id }
                  entryFilterLeadAssigneeOptions { id }
                  entryFilterLeadAuthorOrganizationOptions { id }
                  entryFilterLeadAuthoringOrganizationTypeOptions { id }
                  entryFilterLeadCreatedByOptions { id }
                  entryFilterLeadSourceOrganizationOptions { id }
                  entryFilterModifiedByOptions { id }
                  sourceOrganizationOptions { id }
                }
              }
            }
          }
        }
    '''

    def setUp(self):
        super().setUp()
        self.af = AnalysisFrameworkFactory.create()
        self.region1, self.region2 = RegionFactory.create_batch(2)
        self.project = ProjectFactory.create(analysis_framework=self.af)
        self.project.regions.add(self.region1)
        self.non_member_user = UserFactory.create(email='non-member@x.y')
        self.member_user = UserFactory.create(email='member@x.y')
        self.project.add_member(self.member_user)

        # Create entities used for entryFilterdData
        # -- Geo Data
        geo_widget = WidgetFactory.create(analysis_framework=self.af, widget_id=Widget.WidgetType.GEO)
        geo_widget_filter = AfFilterFactory.create(analysis_framework=self.af, widget_key=geo_widget.key)
        # -- -- Access access here
        admin_level1_1, admin_level1_2 = AdminLevelFactory.create_batch(2, region=self.region1)
        geoarea1_1_1, _ = GeoAreaFactory.create_batch(2, admin_level=admin_level1_1)
        geoarea1_2_1, geoarea1_2_1 = GeoAreaFactory.create_batch(2, admin_level=admin_level1_2)
        # -- -- No access here
        admin_level2 = AdminLevelFactory.create(region=self.region2)
        _, geoarea2_2 = GeoAreaFactory.create_batch(2, admin_level=admin_level2)

        # -- Organizations/ Organization Types
        org_type1, org_type2, org_type3 = OrganizationTypeFactory.create_batch(3)
        org1, org2, org3 = OrganizationFactory.create_batch(3, organization_type=org_type1)
        # -- Users (Members)
        m_user1, m_user2, m_user3, user4 = UserFactory.create_batch(4)
        [self.project.add_member(user) for user in [m_user1, m_user2, m_user3]]

        def _str_list(int_list):
            return [str(_int) for _int in int_list]

        def get_id_obj(objs):
            return [
                dict(id=str(obj.pk)) for obj in objs
            ]

        self.custom_filters = dict(
            assignees=_str_list([m_user1.pk, m_user2.pk]),
            author_organizations=_str_list([org1.pk, org2.pk]),
            authoring_organization_types=_str_list([org_type1.pk, org_type2.pk]),
            created_by=_str_list([m_user1.pk, m_user3.pk]),
            modified_by=_str_list([m_user2.pk, m_user3.pk]),
            source_organizations=_str_list([org2.pk, org3.pk]),
            entries_filter_data=dict(
                created_by=_str_list([m_user2.pk, m_user3.pk, user4.pk]),
                lead_assignees=_str_list([m_user1.pk, m_user3.pk]),
                lead_author_organizations=_str_list([org1.pk, org3.pk]),
                lead_authoring_organization_types=_str_list([org_type2.pk, org_type3.pk]),
                lead_created_by=_str_list([m_user2.pk, m_user3.pk]),
                lead_source_organizations=_str_list([org2.pk, org3.pk]),
                modified_by=_str_list([m_user1.pk, m_user3.pk]),
                filterable_data=[dict(
                    filter_key=geo_widget_filter.key,
                    value_list=_str_list([geoarea1_1_1.pk, geoarea1_2_1.pk, geoarea2_2.pk]),
                )],
            )
        )
        self.custom_filters_camel_case = json.loads(CamelCaseJSONRenderer().render(self.custom_filters))

        self.expected_filter_data_options = dict(
            assigneeOptions=get_id_obj([m_user1, m_user2]),
            authorOrganizationOptions=get_id_obj([org1, org2]),
            authorOrganizationTypeOptions=get_id_obj([org_type1, org_type2]),
            createdByOptions=get_id_obj([m_user1, m_user3]),
            modifiedByOptions=get_id_obj([m_user2, m_user3]),
            sourceOrganizationOptions=get_id_obj([org2, org3]),
            entryFilterCreatedByOptions=get_id_obj([m_user2, m_user3]),
            entryFilterLeadAssigneeOptions=get_id_obj([m_user1, m_user3]),
            entryFilterLeadAuthorOrganizationOptions=get_id_obj([org1, org3]),
            entryFilterLeadAuthoringOrganizationTypeOptions=get_id_obj([org_type2, org_type3]),
            entryFilterLeadCreatedByOptions=get_id_obj([m_user2, m_user3]),
            entryFilterLeadSourceOrganizationOptions=get_id_obj([org2, org3]),
            entryFilterModifiedByOptions=get_id_obj([m_user1, m_user3]),
            entryFilterGeoAreaOptions=get_id_obj([geoarea1_1_1, geoarea1_2_1]),
        )

    def test_user_saved_lead_filter_query(self):
        def _query_check(**kwargs):
            return self.query_check(self.LEAD_FILTER_SAVE_QUERY, variables={'id': str(self.project.id)}, **kwargs)

        # Without login
        _query_check(assert_for_error=True)

        # login with non-member-user
        self.force_login(self.non_member_user)
        content = _query_check()
        self.assertIsNone(content['data']['project']['userSavedLeadFilter'], content)
        UserSavedLeadFilterFactory.create(user=self.non_member_user, project=self.project)

        # Same here as well even with saved filter in backend
        content = _query_check()
        self.assertIsNone(content['data']['project']['userSavedLeadFilter'], content)

        # login with member-user
        self.force_login(self.member_user)
        content = _query_check()
        self.assertIsNone(content['data']['project']['userSavedLeadFilter'], content)

        UserSavedLeadFilterFactory.create(
            user=self.member_user,
            project=self.project,
            filters=self.custom_filters,
        )
        content = _query_check()
        self.assertIsNotNone(content['data']['project']['userSavedLeadFilter'], content)
        self.maxDiff = None
        self.assertEqual(
            content['data']['project']['userSavedLeadFilter']['filtersData'],
            self.expected_filter_data_options,
            content,
        )

    def test_user_saved_lead_filter_mutation(self):
        minput = {
            'title': 'First Filter',
            'filters': {},
        }

        def _query_check(**kwargs):
            return self.query_check(
                self.LEAD_FILTER_SAVE_MUTATION,
                minput=minput,
                mnested=['project'],
                variables={'id': str(self.project.id)},
                **kwargs,
            )

        # Without login
        _query_check(assert_for_error=True)

        # login with non-member-user
        self.force_login(self.non_member_user)
        _query_check(assert_for_error=True)

        # login with member-user
        self.force_login(self.member_user)
        content = _query_check(okay=True)
        self.assertIsNotNone(content['data']['project']['leadFilterSave']['result'], content)

        # With some valid data
        minput['filters'] = self.custom_filters_camel_case
        content = _query_check(okay=True)
        self.assertEqual(
            content['data']['project']['leadFilterSave']['result']['filtersData'],
            self.expected_filter_data_options,
            content,
        )
