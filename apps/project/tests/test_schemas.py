from unittest import mock
from dateutil.relativedelta import relativedelta

from django.utils import timezone
from factory import fuzzy

from utils.graphene.tests import GraphQLTestCase
from user.utils import send_project_join_request_emails

from user.factories import UserFactory
from lead.factories import LeadFactory
from entry.factories import EntryFactory
from project.factories import ProjectFactory, ProjectJoinRequestFactory
from analysis_framework.factories import AnalysisFrameworkFactory
from geo.factories import RegionFactory

from project.tasks import _generate_project_stats_cache
from notification.models import Notification
from project.models import (
    ProjectRole,
    ProjectJoinRequest,
    ProjectMembership
)


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
                  numberOfLeadsTaggedAndControlled
                  numberOfEntries
                  numberOfUsers
                  leadsActivity {
                    count
                    date
                  }
                }
                membershipPending
                regions {
                  id
                  title
                }
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
                "controlled": False,
                "months": -1,
            },
            {
                "lead": lead1_1,
                "controlled": False,
                "months": -3,
            },
            {
                "lead": lead1_2,
                "controlled": True,
                "months": -3,
            },
            {
                "lead": lead1_2,
                "controlled": False,
                "months": -2,
            },
            {
                "lead": lead1_2,
                "controlled": True,
                "months": -2,
            },
            {
                "lead": lead1_3,
                "controlled": True,
                "months": -3,
            },
            {
                "lead": lead1_3,
                "controlled": True,
                "months": -3,
            },

        ]
        now = timezone.now()
        for item in data:
            self.update_obj(
                EntryFactory.create(lead=item['lead'], controlled=item['controlled'],
                                    project=public_project, analysis_framework=analysis_framework),
                created_at=now + relativedelta(months=item['months'])
            )
        EntryFactory.create(lead=lead1_3, project=public_project, controlled=True, analysis_framework=analysis_framework)
        EntryFactory.create(lead=lead1_4, project=public_project, controlled=True, analysis_framework=analysis_framework)

        lead2 = LeadFactory.create(project=public_project2)
        lead3 = LeadFactory.create(project=public_project3)
        EntryFactory.create(lead=lead2, project=public_project2, controlled=False, analysis_framework=analysis_framework)
        EntryFactory.create(lead=lead3, project=public_project3, controlled=False, analysis_framework=analysis_framework)

        user2, user3, request_user, non_member_user = UserFactory.create_batch(4)
        analysis_framework = AnalysisFrameworkFactory.create()
        public_project = ProjectFactory.create()
        private_project = ProjectFactory.create(is_private=True)
        ProjectJoinRequestFactory.create(
            project=public_project, requested_by=request_user,
            status='pending', role=self.project_role_admin
        )

        # add some project member
        public_project.add_member(user)
        public_project.add_member(user2)
        public_project.add_member(user3)

        # add some lead for the project
        lead = LeadFactory.create(project=public_project)
        LeadFactory.create_batch(3, project=public_project)
        LeadFactory.create(project=private_project)

        # add some entry for the project
        EntryFactory.create_batch(
            4,
            project=public_project, analysis_framework=analysis_framework, lead=lead
        )
        EntryFactory.create(project=private_project, analysis_framework=analysis_framework, lead=lead)

        # lets add some regions to project
        region1, region2, region3 = RegionFactory.create_batch(3)
        public_project.regions.add(region1)
        public_project.regions.add(region2)
        private_project.regions.add(region3)

        # Generate project cache
        _generate_project_stats_cache()

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

        # login with non_member
        self.force_login(non_member_user)
        content = self.query_check(query, variables={'id': public_project.id})
        self.assertNotEqual(content['data']['project'], None, content)
        self.assertEqual(content['data']['project']['membershipPending'], False)

        # --- member user
        # ---- (public-project)
        self.force_login(user)
        content = self.query_check(query, variables={'id': public_project.id})
        self.assertNotEqual(content['data']['project'], None, content)
        self.assertEqual(content['data']['project']['stats']['numberOfLeads'], 4, content)
        self.assertEqual(content['data']['project']['stats']['numberOfLeadsTagged'], 1, content)
        self.assertEqual(content['data']['project']['stats']['numberOfLeadsTaggedAndControlled'], 0, content)
        self.assertEqual(content['data']['project']['stats']['numberOfEntries'], 4, content)
        self.assertEqual(content['data']['project']['stats']['numberOfUsers'], 3, content)
        self.assertEqual(len(content['data']['project']['stats']['leadsActivity']), 1, content)
        self.assertEqual(len(content['data']['project']['stats']['entriesActivity']), 1, content)
        self.assertEqual(len(content['data']['project']['regions']), 2, content)
        self.assertListIds(content['data']['project']['regions'], [region1, region2], content)

        # login with request user
        self.force_login(request_user)
        content = self.query_check(query, variables={'id': public_project.id})
        self.assertNotEqual(content['data']['project'], None, content)
        self.assertEqual(content['data']['project']['membershipPending'], True)

        # ---- (private-project)
        self.force_login(user)
        private_project.add_member(user)
        content = self.query_check(query, variables={'id': private_project.id})
        self.assertNotEqual(content['data']['project'], None, content)
        self.assertEqual(len(content['data']['project']['regions']), 1, content)
        self.assertListIds(content['data']['project']['regions'], [region3], content)

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
        EntryFactory.create(lead=lead1, controlled=False,
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


class TestProjectJoinMutation(GraphQLTestCase):
    def setUp(self):
        self.project_join_mutation = '''
            mutation Mutation($input: ProjectJoinRequestInputType!) {
              joinProject(data: $input) {
                ok
                errors
                result {
                  id
                  data
                  project {
                    id
                  }
                  status
                  requestedBy {
                    id
                  }
                }
              }
            }
        '''
        super().setUp()

    @mock.patch(
        'project.serializers.send_project_join_request_emails.delay',
        side_effect=send_project_join_request_emails.delay
    )
    def test_valid_project_join(self, send_project_join_request_emails_mock):
        user = UserFactory.create()
        admin_user = UserFactory.create()
        project = ProjectFactory.create()
        project.add_member(admin_user, role=ProjectRole.get_default_admin_role())
        reason = fuzzy.FuzzyText(length=100).fuzz()
        minput = dict(project=project.id, reason=reason)
        self.force_login(user)
        notification_qs = Notification.objects.filter(
            receiver=admin_user,
            project=project,
            notification_type=Notification.PROJECT_JOIN_REQUEST
        )
        old_count = notification_qs.count()
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(self.project_join_mutation, minput=minput, okay=True)
        self.assertEqual(content['data']['joinProject']['result']['requestedBy']['id'], str(user.id), content)
        self.assertEqual(content['data']['joinProject']['result']['project']['id'], str(project.id), content)
        send_project_join_request_emails_mock.assert_called_once()
        # confirm that the notification is also created
        assert notification_qs.count() > old_count

    def test_already_member_project(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        project.add_member(user)
        reason = fuzzy.FuzzyText(length=100).fuzz()
        minput = dict(project=project.id, reason=reason)
        self.force_login(user)
        content = self.query_check(self.project_join_mutation, minput=minput, okay=False)
        self.assertEqual(len(content['data']['joinProject']['errors']), 1, content)

    def test_project_join_reason_length(self):
        user = UserFactory.create()
        project1, project2 = ProjectFactory.create_batch(2)
        reason = fuzzy.FuzzyText(length=49).fuzz()
        minput = dict(project=project1.id, reason=reason)
        self.force_login(user)
        # Invalid
        content = self.query_check(self.project_join_mutation, minput=minput, okay=False)
        self.assertEqual(len(content['data']['joinProject']['errors']), 1, content)
        # Invalid
        minput['reason'] = fuzzy.FuzzyText(length=501).fuzz()
        content = self.query_check(self.project_join_mutation, minput=minput, okay=False)
        self.assertEqual(len(content['data']['joinProject']['errors']), 1, content)
        # Valid (Project 1) max=500
        minput['reason'] = fuzzy.FuzzyText(length=500).fuzz()
        content = self.query_check(self.project_join_mutation, minput=minput, okay=True)
        self.assertEqual(content['data']['joinProject']['errors'], None, content)
        # Valid (Project 2) min=50
        minput['reason'] = fuzzy.FuzzyText(length=50).fuzz()
        minput['project'] = project2.pk
        content = self.query_check(self.project_join_mutation, minput=minput, okay=True)
        self.assertEqual(content['data']['joinProject']['errors'], None, content)

    def test_join_private_project(self):
        user = UserFactory.create()
        project = ProjectFactory.create(is_private=True)
        reason = fuzzy.FuzzyText(length=50).fuzz()
        minput = dict(project=project.id, reason=reason)
        self.force_login(user)
        content = self.query_check(self.project_join_mutation, minput=minput, okay=False)
        self.assertEqual(len(content['data']['joinProject']['errors']), 1, content)


class TestProjectJoinDeleteMutation(GraphQLTestCase):
    def setUp(self):
        self.project_join_delete_mutation = '''
            mutation Mutation($projectId: ID!) {
              deleteProjectJoin(projectId: $projectId) {
                ok
                errors
                result {
                  data
                  project {
                    id
                  }
                  status
                  requestedBy {
                    id
                  }
                }
              }
            }
        '''
        super().setUp()

    def test_delete_project_join_request(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        ProjectJoinRequestFactory.create(
            requested_by=user,
            project=project,
            role=ProjectRole.get_default_role(),
            status=ProjectJoinRequest.Status.PENDING,
        )
        join_request_qs = ProjectJoinRequest.objects.filter(requested_by=user, project=project)
        old_join_request_count = join_request_qs.count()

        self.force_login(user)
        self.query_check(self.project_join_delete_mutation, variables={'projectId': project.id}, okay=True)
        self.assertEqual(join_request_qs.count(), old_join_request_count - 1)


class TestProjectJoinAcceptRejectMutation(GraphQLTestCase):
    def setUp(self):
        self.projet_accept_reject_mutation = '''
            mutation MyMutation ($projectId: ID! $joinRequestId: ID! $input: ProjectAcceptRejectInputType!) {
              project(id: $projectId) {
                acceptRejectProject(id: $joinRequestId, data: $input) {
                  ok
                  errors
                  result {
                    data
                    project {
                      id
                    }
                    status
                    requestedBy {
                      id
                    }
                    respondedBy {
                      id
                    }
                  }
                }
              }
            }
        '''
        super().setUp()

    def test_project_join_request_accept(self):
        user = UserFactory.create()
        user2 = UserFactory.create()
        project = ProjectFactory.create()
        project.add_member(user, role=self.project_role_admin)
        join_request = ProjectJoinRequestFactory.create(requested_by=user2,
                                                        project=project,
                                                        role=ProjectRole.get_default_role(),
                                                        status=ProjectJoinRequest.Status.PENDING)
        minput = dict(status='accepted', role='normal')

        # without login
        self.query_check(
            self.projet_accept_reject_mutation,
            minput=minput,
            variables={'projectId': project.id, 'joinRequestId': join_request.id},
            assert_for_error=True
        )

        # with login
        self.force_login(user)
        content = self.query_check(self.projet_accept_reject_mutation, minput=minput,
                                   variables={'projectId': project.id, 'joinRequestId': join_request.id})
        self.assertEqual(
            content['data']['project']['acceptRejectProject']['result']['requestedBy']['id'],
            str(user2.id), content
        )
        self.assertEqual(
            content['data']['project']['acceptRejectProject']['result']['respondedBy']['id'],
            str(user.id), content
        )
        self.assertEqual(content['data']['project']['acceptRejectProject']['result']['status'], 'ACCEPTED', content)
        # make sure memberships is created
        self.assertIn(user2.id, ProjectMembership.objects.filter(project=project).values_list('member', flat=True))

    def test_project_join_request_reject(self):
        user = UserFactory.create()
        user2 = UserFactory.create()
        project = ProjectFactory.create()
        project.add_member(user, role=self.project_role_admin)
        join_request = ProjectJoinRequestFactory.create(requested_by=user2,
                                                        project=project,
                                                        role=ProjectRole.get_default_role(),
                                                        status=ProjectJoinRequest.Status.PENDING)
        minput = dict(status='rejected')
        # without login
        self.query_check(
            self.projet_accept_reject_mutation,
            minput=minput,
            variables={'projectId': project.id, 'joinRequestId': join_request.id},
            assert_for_error=True
        )

        # with login
        self.force_login(user)
        content = self.query_check(self.projet_accept_reject_mutation, minput=minput,
                                   variables={'projectId': project.id, 'joinRequestId': join_request.id})
        self.assertEqual(content['data']['project']['acceptRejectProject']['result']['status'], 'REJECTED', content)
