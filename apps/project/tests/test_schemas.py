from dateutil.relativedelta import relativedelta

from django.utils import timezone

from utils.graphene.tests import GraphQLTestCase

from user.factories import UserFactory
from lead.factories import LeadFactory
from entry.factories import EntryFactory
from project.factories import ProjectFactory
from analysis_framework.factories import AnalysisFrameworkFactory

from project.tasks import _generate_project_stats_cache
from project.models import ProjectJoinRequest


class TestProjectSchema(GraphQLTestCase):
    def test_project_query(self):
        """
        Test private + non-private project behaviour
        """
        query = '''
            query MyQuery ($id: ID!) {
              project(id: $id) {
                id
                title
                currentUserRole
                startDate
                statsCache
                status
                isVisualizationEnabled
                isPrivate
                endDate
                description
                data
                stats {
                  entriesActivity {
                    count
                    date
                  }
                  numberOfLeads
                  numberOfLeadsTagged
                  numberOfLeadsTaggedAndVerified
                  numberOfEntries
                  leadsActivity {
                    count
                    date
                  }
                }
                membersCount
                userStatus
                sourcesCount
                entriesCount
              }
            }
        '''

        user = UserFactory.create()
        public_project, public_project2, public_project3 = ProjectFactory.create_batch(3)
        analysis_framework = AnalysisFrameworkFactory.create()
        now = timezone.now()
        lead1_1 = self.update_obj(LeadFactory.create(project=public_project), created_at=now + relativedelta(months=-1))
        lead1_2 = self.update_obj(LeadFactory.create(project=public_project), created_at=now + relativedelta(months=-2))
        lead1_3 = self.update_obj(LeadFactory.create(project=public_project), created_at=now + relativedelta(months=-2))
        lead1_4 = self.update_obj(LeadFactory.create(project=public_project), created_at=now + relativedelta(months=-1))
        self.update_obj(LeadFactory.create(project=public_project), created_at=now + relativedelta(months=-1))

        data = [
            {
                "lead": lead1_1,
                "verified": False,
                "months": -1,
            },
            {
                "lead": lead1_1,
                "verified": False,
                "months": -3,
            },
            {
                "lead": lead1_2,
                "verified": True,
                "months": -3,
            },
            {
                "lead": lead1_2,
                "verified": False,
                "months": -2,
            },
            {
                "lead": lead1_2,
                "verified": True,
                "months": -2,
            },
            {
                "lead": lead1_3,
                "verified": True,
                "months": -3,
            },
            {
                "lead": lead1_3,
                "verified": True,
                "months": -3,
            },

        ]
        now = timezone.now()
        for item in data:
            self.update_obj(
                EntryFactory.create(lead=item['lead'], verified=item['verified'],
                                    project=public_project, analysis_framework=analysis_framework),
                created_at=now + relativedelta(months=item['months'])
            )
        EntryFactory.create(lead=lead1_3, project=public_project, verified=True, analysis_framework=analysis_framework)
        EntryFactory.create(lead=lead1_4, project=public_project, verified=True, analysis_framework=analysis_framework)

        lead2 = LeadFactory.create(project=public_project2)
        lead3 = LeadFactory.create(project=public_project3)
        EntryFactory.create(lead=lead2, project=public_project2, verified=False, analysis_framework=analysis_framework)
        EntryFactory.create(lead=lead3, project=public_project3, verified=False, analysis_framework=analysis_framework)

        # Generate project cache
        _generate_project_stats_cache()

        user2 = UserFactory.create()
        user3 = UserFactory.create()
        request_user = UserFactory.create()
        non_member_user = UserFactory.create()

        public_project = ProjectFactory.create()
        private_project = ProjectFactory.create(is_private=True)
        ProjectJoinRequest.objects.create(project=public_project, requested_by=request_user,
                                          status='pending', role=self.project_role_admin)

        # add some project member
        public_project.add_member(user)
        public_project.add_member(user2)
        public_project.add_member(user3)

        # add some lead for the project
        LeadFactory.create(project=public_project)
        LeadFactory.create(project=public_project)
        LeadFactory.create(project=public_project)
        LeadFactory.create(project=public_project)
        LeadFactory.create(project=private_project)

        # add some entry for the project
        EntryFactory.create(project=public_project)
        EntryFactory.create(project=public_project)
        EntryFactory.create(project=public_project)
        EntryFactory.create(project=public_project)
        EntryFactory.create(project=private_project)

        # -- Without login
        self.query_check(query, assert_for_error=True, variables={'id': public_project.id})
        self.query_check(query, assert_for_error=True, variables={'id': private_project.id})

        # -- With login
        self.force_login(user)

        # --- non-member user
        content = self.query_check(query, variables={'id': public_project.id})
        self.assertNotEqual(content['data']['project'], None, content)
        content = self.query_check(query, variables={'id': private_project.id})
        self.assertEqual(content['data']['project'], None, content)

        # --- member user
        # ---- (public-project)
        content = self.query_check(query, variables={'id': public_project.id})
        self.assertNotEqual(content['data']['project'], None, content)
        self.assertEqual(content['data']['project']['stats']['numberOfLeads'], 5, content)
        self.assertEqual(content['data']['project']['stats']['numberOfLeadsTagged'], 4, content)
        self.assertEqual(content['data']['project']['stats']['numberOfLeadsTaggedAndVerified'], 2, content)
        self.assertEqual(content['data']['project']['stats']['numberOfEntries'], 9, content)
        self.assertEqual(len(content['data']['project']['stats']['leadsActivity']), 2, content)
        self.assertEqual(len(content['data']['project']['stats']['entriesActivity']), 3, content)
        self.assertEqual(content['data']['project']['membersCount'], 3)
        self.assertEqual(content['data']['project']['sourcesCount'], 4)
        self.assertEqual(content['data']['project']['entriesCount'], 4)
        self.assertEqual(content['data']['project']['userStatus'], 'member')

        # login with request user
        self.force_login(request_user)
        content = self.query_check(query, variables={'id': public_project.id})
        self.assertNotEqual(content['data']['project'], None, content)
        self.assertEqual(content['data']['project']['userStatus'], 'pending')

        # login with non_member
        self.force_login(non_member_user)
        content = self.query_check(query, variables={'id': public_project.id})
        self.assertNotEqual(content['data']['project'], None, content)
        self.assertEqual(content['data']['project']['userStatus'], 'non_member')

        # ---- (private-project)
        self.force_login(user)
        private_project.add_member(user)
        content = self.query_check(query, variables={'id': private_project.id})
        self.assertNotEqual(content['data']['project'], None, content)
        self.assertEqual(content['data']['project']['membersCount'], 1)
        self.assertEqual(content['data']['project']['sourcesCount'], 1)
        self.assertEqual(content['data']['project']['entriesCount'], 1)

    def test_projects_query(self):
        """
        Test private + non-private project list behaviour
        """
        query = '''
            query MyQuery {
              projects (ordering: "id") {
                page
                pageSize
                totalCount
                results {
                  id
                  status
                  title
                  isPrivate
                  description
                  currentUserRole
                }
              }
            }
        '''

        user = UserFactory.create()
        public_project = ProjectFactory.create()
        private_project = ProjectFactory.create(is_private=True)

        # -- Without login
        self.query_check(query, assert_for_error=True)

        # -- With login
        self.force_login(user)

        # --- non-member user (only public project is listed)
        content = self.query_check(query)
        self.assertEqual(content['data']['projects']['totalCount'], 1, content)
        self.assertEqual(content['data']['projects']['results'][0]['id'], str(public_project.pk), content)

        # --- member user (all public project is listed)
        public_project.add_member(user)
        private_project.add_member(user)
        content = self.query_check(query)
        self.assertEqual(content['data']['projects']['totalCount'], 2, content)
        self.assertEqual(content['data']['projects']['results'][0]['id'], str(public_project.pk), content)
        self.assertEqual(content['data']['projects']['results'][1]['id'], str(private_project.pk), content)

    def test_project_stat_recent(self):
        query = '''
              query MyQuery {
                recentProjects {
                  id
                  status
                  title
                  isPrivate
                  description
                  currentUserRole
                }
              }
          '''

        user = UserFactory.create()
        analysis_framework = AnalysisFrameworkFactory.create()
        public_project1, public_project2, public_project3, public_project4 = ProjectFactory.create_batch(4)
        public_project1.add_member(user)
        public_project2.add_member(user)
        public_project3.add_member(user)

        lead1 = LeadFactory.create(project=public_project1, created_by=user)
        LeadFactory.create(project=public_project2, created_by=user)
        EntryFactory.create(lead=lead1, verified=False,
                            created_by=user, project=public_project1,
                            analysis_framework=analysis_framework)
        LeadFactory.create(project=public_project3, created_by=user)
        LeadFactory.create(project=public_project4, created_by=user)
        # -- Without login
        self.query_check(query, assert_for_error=True)

        # -- With login
        self.force_login(user)

        content = self.query_check(query)
        self.assertEqual(len(content['data']['recentProjects']), 3, content)
        self.assertEqual(content['data']['recentProjects'][0]['id'], str(public_project3.pk), content)
        self.assertEqual(content['data']['recentProjects'][1]['id'], str(public_project1.pk), content)
        self.assertEqual(content['data']['recentProjects'][2]['id'], str(public_project2.pk), content)


class TestProjectFilterSchema(GraphQLTestCase):
    def test_project_query_filter(self):
        query = '''
            query MyQuery ($isCurrentUserMember: Boolean!) {
              projects(isCurrentUserMember: $isCurrentUserMember) {
                page
                pageSize
                totalCount
                results {
                  id
                  title
                  isPrivate
                  currentUserRole
                }
              }
            }
        '''

        user = UserFactory.create()
        project1 = ProjectFactory.create()
        project2 = ProjectFactory.create(is_private=True)
        project3 = ProjectFactory.create()
        ProjectFactory.create(is_private=True)

        # Add user to project1 only (one normal + one private)
        project1.add_member(user)
        project2.add_member(user)

        # -- Without login
        self.query_check(query, variables={'isCurrentUserMember': True}, assert_for_error=True)

        # -- With login
        self.force_login(user)

        # project without membership
        content = self.query_check(query, variables={'isCurrentUserMember': True})
        self.assertEqual(content['data']['projects']['totalCount'], 2, content)
        self.assertListIds(content['data']['projects']['results'], [project1, project2], content)
        # project with membership
        content = self.query_check(query, variables={'isCurrentUserMember': False})
        self.assertEqual(content['data']['projects']['totalCount'], 1, content)  # Private will not show here
        self.assertListIds(content['data']['projects']['results'], [project3], content)
