from unittest import mock

from factory import fuzzy

from utils.graphene.tests import GraphQLTestCase
from user.utils import send_project_join_request_emails
from notification.models import Notification
from project.models import (
    ProjectRole,
    ProjectJoinRequest,
    ProjectMembership
)

from user.factories import UserFactory
from project.factories import ProjectFactory, ProjectJoinRequestFactory


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

    def test_already_request_sent_for_project(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        # lets create a join request for the project
        ProjectJoinRequestFactory.create(
            requested_by=user,
            project=project,
            role=ProjectRole.get_default_role(),
            status=ProjectJoinRequest.Status.PENDING,
        )
        reason = fuzzy.FuzzyText(length=50).fuzz()
        minput = dict(project=project.id, reason=reason)
        self.force_login(user)
        content = self.query_check(self.project_join_mutation, minput=minput, okay=False)
        self.assertEqual(len(content['data']['joinProject']['errors']), 1, content)


class TestProjectJoinDeleteMutation(GraphQLTestCase):
    def setUp(self):
        self.project_join_request_delete_mutation = '''
            mutation Mutation($projectId: ID!) {
              projectJoinRequestDelete(projectId: $projectId) {
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
        self.query_check(self.project_join_request_delete_mutation, variables={'projectId': project.id}, okay=True)
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
