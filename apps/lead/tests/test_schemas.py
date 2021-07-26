from utils.graphene.tests import GraphQLTestCase, GraphQLSnapShotTestCase

from organization.factories import OrganizationTypeFactory, OrganizationFactory
from user.factories import UserFactory
from project.factories import ProjectFactory
from gallery.factories import FileFactory

from lead.models import Lead
from lead.factories import LeadFactory, EmmEntityFactory


class TestLeadQuerySchema(GraphQLTestCase):
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
        project.add_member(member_user, role=self.role_viewer_non_confidential)
        project.add_member(confidential_member_user, role=self.role_viewer)
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
        project.add_member(member_user, role=self.role_viewer_non_confidential)
        project.add_member(confidential_member_user, role=self.role_viewer)
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

    def test_leads_fields_query(self):
        """
        Test leads field value
        """
        query = '''
            query MyQuery ($id: ID!) {
              project(id: $id) {
                leads(ordering: "id") {
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
                    verifiedStat {
                      totalCount
                      verifiedCount
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

        project = ProjectFactory.create()
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

        # -- With login
        self.force_login(user)

        # --- member user (only unprotected leads)
        self.force_login(user)
        content = self.query_check(query, variables={'id': project.id})
        results = content['data']['project']['leads']['results']
        # Count check
        self.assertEqual(content['data']['project']['leads']['totalCount'], 2, content)
        self.assertListIds(results, [lead1, lead2], content)
        self.assertEqual(len(results[0]['authors']), 0, content)
        # Source check
        self.assertIdEqual(results[0]['source']['id'], org1.id, content)
        self.assertEqual(results[0]['source']['logo']['file']['name'], str(org1.logo.file.name), content)
        self.assertEqual(results[0]['source']['logo']['file']['url'], self.get_media_url(org1.logo.file.name), content)
        # Authors check
        self.assertListIds(results[1]['authors'], [org1, org3], content)
        self.assertIdEqual(results[1]['source']['mergedAs']['id'], org1.id, content)


class TestLeadMutationSchema(GraphQLTestCase):
    CREATE_LEAD_QUERY = '''
        mutation MyMutation ($projectId: ID!, $input: LeadInputType!) {
          project(id: $projectId) {
            leadCreate1: leadCreate(data: $input) {
              ok
              errors
              result {
                id
                title
                confidentiality
                priority
                publishedOn
                sourceType
                status
                text
                url
                website
                source {
                    id
                }
                authors {
                    id
                }
                assignee {
                    id
                }
                emmEntities {
                    name
                }
                emmTriggers {
                    emmKeyword
                    emmRiskFactor
                    count
                }
              }
            }
          }
        }
    '''

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        # User with role
        self.non_member_user = UserFactory.create()
        self.readonly_member_user = UserFactory.create()
        self.member_user = UserFactory.create()
        self.project.add_member(self.readonly_member_user, role=self.role_viewer_non_confidential)
        self.project.add_member(self.member_user, role=self.role_analyst)

    def test_lead_create(self):
        """
        This test makes sure only valid users can create lead
        """
        def _query_check(minput, **kwargs):
            return self.query_check(
                self.CREATE_LEAD_QUERY,
                minput=minput,
                variables={'projectId': self.project.id},
                **kwargs
            )

        minput = dict(
            title='Lead Title 101',
        )
        # -- Without login
        _query_check(minput, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(minput, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(minput, assert_for_error=True)

        # --- member user
        self.force_login(self.member_user)
        content = _query_check(minput)['data']['project']['leadCreate1']['result']
        self.assertEqual(content['title'], minput['title'], content)

    def test_lead_create_validation(self):
        """
        This test checks create lead validations
        """
        other_file = FileFactory.create()
        our_file = FileFactory.create(created_by=self.member_user)
        org1 = OrganizationFactory.create()
        org2 = OrganizationFactory.create()

        emm_entity_1 = EmmEntityFactory.create()
        emm_entity_2 = EmmEntityFactory.create()

        minput = dict(
            title='Lead Title 101',
            confidentiality=self.genum(Lead.Confidentiality.UNPROTECTED),
            priority=self.genum(Lead.Priority.MEDIUM),
            status=self.genum(Lead.Status.PENDING),
            publishedOn='2020-09-25',
            source=org2.pk,
            authors=[org1.pk, org2.pk],
            text='Random Text',
            url='',
            website='',
            emmEntities=[
                dict(name=emm_entity_1.name),
                dict(name=emm_entity_2.name),
            ],
            emmTriggers=[
                # Return order is by count so let's keep higher count first
                dict(emmKeyword='emm-keyword-1', emmRiskFactor='emm-risk-factor-1', count=20),
                dict(emmKeyword='emm-keyword-2', emmRiskFactor='emm-risk-factor-2', count=10),
            ],
        )

        def _query_check(**kwargs):
            return self.query_check(
                self.CREATE_LEAD_QUERY,
                minput=minput,
                mnested=['project'],
                variables={'projectId': self.project.id},
                **kwargs,
            )

        # --- login
        self.force_login(self.member_user)

        # ------ Non member assignee
        minput['sourceType'] = self.genum(Lead.SourceType.TEXT)
        minput['text'] = 'Text 123'
        minput['assignee'] = self.non_member_user.pk
        result = _query_check(okay=False)['data']['project']['leadCreate1']['result']
        self.assertEqual(result, None, result)
        # ------ Member assignee (TODO: Test partial update as well) + Text Test
        minput['assignee'] = self.member_user.pk
        minput['text'] = 'Text 123123'  # Need to provide different text
        result = _query_check(okay=True)['data']['project']['leadCreate1']['result']
        self.assertIdEqual(result['assignee']['id'], minput['assignee'], result)
        self.assertCustomDictEqual(result, minput, result, ignore_keys=['id', 'source', 'authors', 'assignee'])
        self.assertIdEqual(result['source']['id'], minput['source'], result)
        self.assertListIds(result['authors'], minput['authors'], result, get_excepted_list_id=lambda x: str(x))
        # ------ Disk
        # File not-owned
        minput['sourceType'] = self.genum(Lead.SourceType.DISK)
        minput['attachment'] = other_file.pk
        result = _query_check(okay=False)['data']['project']['leadCreate1']['result']
        self.assertEqual(result, None, result)
        # File owned
        minput['sourceType'] = self.genum(Lead.SourceType.DISK)
        minput['attachment'] = our_file.pk
        result = _query_check(okay=True)['data']['project']['leadCreate1']['result']
        self.assertEqual(result['title'], minput['title'], result)

        # -------- Duplicate leads validations
        # ------------- Text (Using duplicate text)
        minput['sourceType'] = self.genum(Lead.SourceType.TEXT)
        result = _query_check(okay=False)['data']['project']['leadCreate1']['result']
        self.assertEqual(result, None, result)
        # ------------- Website
        minput['sourceType'] = self.genum(Lead.SourceType.WEBSITE)
        minput['url'] = 'http://www.example.com/random-path'
        minput['website'] = 'www.example.com'
        result = _query_check(okay=True)['data']['project']['leadCreate1']['result']
        self.assertCustomDictEqual(result, minput, result, only_keys=['url', 'website'])
        # Try again will end in error
        result = _query_check(okay=False)['data']['project']['leadCreate1']['result']
        self.assertEqual(result, None, result)
        # ------------- Attachment
        minput['sourceType'] = self.genum(Lead.SourceType.DISK)
        minput['attachment'] = our_file.pk  # Already created this above resulting in error
        result = _query_check(okay=False)['data']['project']['leadCreate1']['result']
        self.assertEqual(result, None, result)

    def test_lead_delete_validation(self):
        """
        This test checks create lead validations
        """
        query = '''
            mutation MyMutation ($projectId: ID! $leadId: ID!) {
              project(id: $projectId) {
                leadDelete(id: $leadId) {
                  ok
                  errors
                  result {
                    id
                    title
                    url
                  }
                }
              }
            }
        '''

        non_access_lead = LeadFactory.create()
        lead = LeadFactory.create(project=self.project)

        def _query_check(lead, will_delete=False, **kwargs):
            result = self.query_check(
                query,
                mnested=['project'],
                variables={'projectId': self.project.id, 'leadId': lead.id},
                **kwargs,
            )
            if will_delete:
                with self.assertRaises(Lead.DoesNotExist):
                    lead.refresh_from_db()
            else:
                lead.refresh_from_db()
            return result

        # Error without login
        _query_check(non_access_lead, assert_for_error=True)

        # --- login
        self.force_login(self.member_user)
        # Error with login (if non-member project)
        _query_check(non_access_lead, assert_for_error=True)
        # ------- login as readonly_member
        self.force_login(self.readonly_member_user)
        # Success with normal lead (with project membership)
        _query_check(lead, assert_for_error=True)
        # ------- login as normal member
        self.force_login(self.member_user)
        # Success with normal lead (with project membership)
        result = _query_check(lead, will_delete=True, okay=True)['data']['project']['leadDelete']['result']
        self.assertEqual(result['title'], lead.title, result)

    def test_lead_update_validation(self):
        query = '''
            mutation MyMutation ($projectId: ID! $leadId: ID! $input: LeadInputType!) {
              project(id: $projectId) {
                leadUpdate(id: $leadId data: $input) {
                  ok
                  errors
                  result {
                    id
                    title
                    sourceType
                    text
                    url
                    website
                    attachment {
                        id
                    }
                    assignee {
                        id
                    }
                    emmEntities {
                        name
                    }
                    emmTriggers {
                        emmKeyword
                        emmRiskFactor
                        count
                    }
                  }
                }
              }
            }
        '''

        lead = LeadFactory.create(project=self.project)
        non_access_lead = LeadFactory.create()
        user_file = FileFactory.create(created_by=self.member_user)

        minput = dict(title='New Lead')

        def _query_check(_lead, **kwargs):
            return self.query_check(
                query,
                minput=minput,
                mnested=['project'],
                variables={'projectId': self.project.id, 'leadId': _lead.id},
                **kwargs,
            )

        # --- without login
        _query_check(lead, assert_for_error=True)

        # --- login
        self.force_login(self.member_user)
        # ------- Non access lead
        _query_check(non_access_lead, assert_for_error=True)
        # ------- Access lead
        result = _query_check(lead, okay=True)['data']['project']['leadUpdate']['result']
        self.assertEqual(result['title'], minput['title'], result)
        # -------- Duplicate leads validations
        # ------------ Text (Using duplicate text)
        new_lead = LeadFactory.create(project=self.project)
        minput['sourceType'] = self.genum(Lead.SourceType.TEXT)
        minput['text'] = new_lead.text
        result = _query_check(lead, okay=False)['data']['project']['leadUpdate']['result']
        self.assertEqual(result, None, result)
        new_lead.delete()  # Can save after deleting the conflicting lead.
        result = _query_check(lead, okay=True)['data']['project']['leadUpdate']['result']
        self.assertEqual(result['title'], minput['title'], result)
        # ------------ Website (Using duplicate website)
        new_lead = LeadFactory.create(
            project=self.project, source_type=Lead.SourceType.WEBSITE,
            url='https://example.com/random-path', website='example.com',
        )
        minput['sourceType'] = self.genum(Lead.SourceType.WEBSITE)
        minput['url'] = new_lead.url
        minput['website'] = new_lead.website
        result = _query_check(lead, okay=False)['data']['project']['leadUpdate']['result']
        self.assertEqual(result, None, result)
        new_lead.delete()  # Can save after deleting the conflicting lead.
        result = _query_check(lead, okay=True)['data']['project']['leadUpdate']['result']
        self.assertEqual(result['url'], minput['url'], result)
        self.assertEqual(result['website'], minput['website'], result)
        # ------------ Attachment (Using duplicate file)
        new_lead = LeadFactory.create(project=self.project, source_type=Lead.SourceType.DISK, attachment=user_file)
        minput['sourceType'] = self.genum(Lead.SourceType.DISK)
        minput['attachment'] = new_lead.attachment.pk
        result = _query_check(lead, okay=False)['data']['project']['leadUpdate']['result']
        self.assertEqual(result, None, result)
        new_lead.delete()  # Can save after deleting the conflicting lead.
        result = _query_check(lead, okay=True)['data']['project']['leadUpdate']['result']
        self.assertIdEqual(result['attachment']['id'], minput['attachment'], result)


class TestLeadBulkMutationSchema(GraphQLSnapShotTestCase):
    factories_used = [UserFactory, ProjectFactory, LeadFactory]

    def test_lead_bulk(self):
        query = '''
        mutation MyMutation ($projectId: ID! $input: [BulkLeadInputType]!) {
          project(id: $projectId) {
            leadBulk(items: $input) {
              errors
              result {
                id
                title
                clientId
              }
            }
          }
        }
        '''
        project = ProjectFactory.create()
        # User with role
        user = UserFactory.create()
        project.add_member(user, role=self.role_analyst)
        lead1 = LeadFactory.create(project=project)
        lead2 = LeadFactory.create(project=project, source_type=Lead.SourceType.WEBSITE, url='https://example.com/path')

        lead_count = Lead.objects.count()
        minput = [
            dict(title='Lead title 1', clientId='new-lead-1'),
            dict(title='Lead title 2', clientId='new-lead-2'),
            dict(
                title='Lead title 4', sourceType=self.genum(Lead.SourceType.WEBSITE), url='https://example.com/path',
                clientId='new-lead-3',
            ),
            dict(id=str(lead1.pk), title='Lead title 3'),
            dict(id=str(lead2.pk), title='Lead title 4'),
        ]

        def _query_check(**kwargs):
            return self.query_check(query, minput=minput, variables={'projectId': project.pk}, **kwargs)

        # --- without login
        _query_check(assert_for_error=True)

        # --- with login
        self.force_login(user)
        response = _query_check()['data']['project']['leadBulk']
        return
        self.assertMatchSnapshot(response)
        self.assertEqual(lead_count + 2, Lead.objects.count())
