from unittest import mock

from factory import fuzzy

from utils.graphene.tests import GraphQLTestCase, GraphQLSnapShotTestCase
from user.utils import send_project_join_request_emails
from notification.models import Notification
from project.models import (
    get_default_role_id,
    ProjectRole,
    ProjectJoinRequest,
    ProjectMembership,
    ProjectUserGroupMembership,
    ProjectStats,
)

from user.factories import UserFactory
from lead.factories import LeadFactory
from entry.factories import EntryFactory, EntryAttributeFactory
from analysis_framework.factories import AnalysisFrameworkFactory, WidgetFactory
from user_group.factories import UserGroupFactory
from project.factories import ProjectFactory, ProjectJoinRequestFactory

from project.tasks import _generate_project_viz_stats
from . import entry_stats_data


class TestProjectGeneralMutation(GraphQLTestCase):
    ENABLE_NOW_PATCHER = True

    @staticmethod
    def set_project_viz_configuration(project):
        w_data = entry_stats_data.WIDGET_DATA
        a_data = entry_stats_data.ATTRIBUTE_DATA

        lead = LeadFactory.create(project=project)
        entry = EntryFactory.create(lead=lead)
        af = project.analysis_framework

        # Create widgets, attributes and configs
        invalid_stat_config = {}
        valid_stat_config = {}

        for index, (title, widget_identifier, data_identifier, config_kwargs) in enumerate([
            ('widget 1d', 'widget_1d', 'matrix1dWidget', {}),
            ('widget 2d', 'widget_2d', 'matrix2dWidget', {}),
            ('geo widget', 'geo_widget', 'geoWidget', {}),
            (
                'severity widget',
                'severity_widget',
                'conditionalWidget',
                {
                    'is_conditional_widget': True,
                    'selectors': ['widgets', 0, 'widget'],
                    'widget_key': 'scalewidget-1',
                    'widget_type': 'scaleWidget',
                },
            ),
            ('reliability widget', 'reliability_widget', 'scaleWidget', {}),
            ('affected groups widget', 'affected_groups_widget', 'multiselectWidget', {}),
            ('specific needs groups widget', 'specific_needs_groups_widget', 'multiselectWidget', {}),
        ]):
            widget = WidgetFactory.create(
                analysis_framework=af,
                section=None,
                title=title,
                widget_id=data_identifier,
                key=f'{data_identifier}-{index}',
                properties={'data': w_data[data_identifier]},
            )
            EntryAttributeFactory.create(entry=entry, widget=widget, data=a_data[data_identifier])
            valid_stat_config[widget_identifier] = {
                'pk': widget.pk,
                **config_kwargs,
            }
            invalid_stat_config[widget_identifier] = {'pk': 0}

        af.properties = {'stats_config': invalid_stat_config}
        af.save(update_fields=('properties',))

        project.is_visualization_enabled = True
        project.save(update_fields=('is_visualization_enabled',))

    def test_projects_viz_configuration_update(self):
        query = '''
            mutation MyMutation($id: ID!, $input: ProjectVizConfigurationInputType!) {
              project(id: $id) {
                projectVizConfigurationUpdate(data: $input) {
                  ok
                  errors
                  result {
                    dataUrl
                    modifiedAt
                    publicShare
                    publicUrl
                    status
                  }
                }
              }
            }
        '''

        normal_user = UserFactory.create()
        admin_user = UserFactory.create()
        member_user = UserFactory.create()
        af = AnalysisFrameworkFactory.create()
        project = ProjectFactory.create(analysis_framework=af)

        self.set_project_viz_configuration(project)
        project.add_member(admin_user, role=self.project_role_admin)
        project.add_member(member_user, role=self.project_role_analyst)

        minput = dict(action=None)

        def _query_check(**kwargs):
            return self.query_check(
                query,
                minput=minput,
                mnested=['project'],
                variables={'id': project.id},
                **kwargs,
            )

        Action = ProjectStats.Action
        _generate_project_viz_stats(project.pk)
        # Check permission for token generation
        for action in [Action.NEW, Action.OFF, Action.NEW, Action.ON]:
            for user, assertLogic in [
                (normal_user, self.assert_403),
                (member_user, self.assert_403),
                (admin_user, self.assert_200),
            ]:
                self.force_login(user)
                current_stats = project.project_stats
                minput['action'] = self.genum(action)
                if assertLogic == self.assert_200:
                    content = _query_check(okay=True)
                else:
                    _query_check(assert_for_error=True)
                    continue
                response = content['data']['project']['projectVizConfigurationUpdate']['result']
                if assertLogic == self.assert_200:
                    if action == 'new':
                        assert response['publicUrl'] != current_stats.token
                        # Logout and check if response is okay
                        self.client.logout()
                        rest_response = self.client.get(f"{response['publicUrl']}?format=json")
                        self.assert_200(rest_response)
                    elif action == 'on':
                        assert (
                            response['publicUrl'] is not None
                        ) or (
                            response['publicUrl'] == current_stats.token
                        )
                        # Logout and check if response is not okay
                        self.client.logout()
                        rest_response = self.client.get(f"{response['publicUrl']}?format=json")
                        self.assert_200(rest_response)
                    elif action == 'off':
                        assert (
                            response['publicUrl'] is not None
                        ) or (
                            response['publicUrl'] == current_stats.token
                        )
                        # Logout and check if response is not okay
                        self.client.logout()
                        rest_response = self.client.get(f"{response['publicUrl']}?format=json")
                        self.assert_403(rest_response)


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
            notification_type=Notification.Type.PROJECT_JOIN_REQUEST
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


class TestProjectMembershipMutation(GraphQLSnapShotTestCase):

    def _user_membership_bulk(self, user_role):
        query = '''
          mutation MyMutation(
              $id: ID!,
              $projectMembership: [BulkProjectMembershipInputType!],
              $projectMembershipDelete: [ID!]!
          ) {
          project(id: $id) {
            id
            title
            projectUserMembershipBulk(items: $projectMembership, deleteIds: $projectMembershipDelete) {
              errors
              result {
                id
                clientId
                joinedAt
                addedBy {
                  id
                  displayName
                }
                role {
                  id
                  title
                }
                member {
                  id
                  displayName
                }
                badges
              }
              deletedResult {
                id
                clientId
                joinedAt
                member {
                  id
                  displayName
                }
                role {
                  id
                  title
                  level
                }
                addedBy {
                  id
                  displayName
                }
                badges
              }
            }
          }
        }
        '''
        creater_user = UserFactory.create()
        user = UserFactory.create()
        low_permission_user = UserFactory.create()
        non_member_user = UserFactory.create()

        (
            member_user0,
            member_user1,
            member_user2,
            member_user3,
            member_user4,
            member_user5,
            member_user6,
        ) = UserFactory.create_batch(7)

        project = ProjectFactory.create(created_by=creater_user)
        membership1 = project.add_member(member_user1, badges=[ProjectMembership.BadgeType.QA])
        membership2 = project.add_member(member_user2)
        project.add_member(member_user5)
        creater_user_membership = project.add_member(creater_user, role=self.project_role_clairvoyant_one)
        another_clairvoyant_user = project.add_member(member_user0, role=self.project_role_clairvoyant_one)
        user_membership = project.add_member(user, role=user_role)
        project.add_member(low_permission_user)

        minput = dict(
            projectMembershipDelete=[
                str(membership1.pk),  # This will be only on try 1
                # This shouldn't be on any response (requester + creater)
                str(user_membership.pk),
                str(creater_user_membership.pk),
                str(another_clairvoyant_user.pk),
            ],
            projectMembership=[
                # Try updating membership (Valid on try 1, invalid on try 2)
                dict(
                    member=member_user2.pk,
                    clientId="member-user-2",
                    role=self.project_role_clairvoyant_one.pk,
                    id=membership2.pk,
                    badges=[self.genum(ProjectMembership.BadgeType.QA)],
                ),
                # Try adding already existing member
                dict(
                    member=member_user5.pk,
                    clientId="member-user-5",
                    role=self.project_role_analyst.pk,
                ),
                # Try adding new member (Valid on try 1, invalid on try 2)
                dict(
                    member=member_user3.pk,
                    clientId="member-user-3",
                    role=self.project_role_analyst.pk,
                ),
                # Try adding new member (without giving role) -> this should use default role
                # Valid on try 1, invalid on try 2
                dict(
                    member=member_user4.pk,
                    clientId="member-user-4",
                ),
            ],
        )

        def _query_check(**kwargs):
            return self.query_check(
                query,
                mnested=['project'],
                variables={'id': project.id, **minput},
                **kwargs,
            )
        # ---------- Without login
        _query_check(assert_for_error=True)
        # ---------- With login (with non-member)
        self.force_login(non_member_user)
        _query_check(assert_for_error=True)
        # ---------- With login (with low-permission member)
        self.force_login(non_member_user)
        _query_check(assert_for_error=True)
        # ---------- With login (with higher permission)
        self.force_login(user)
        # ----------------- Some Invalid input
        response = _query_check()['data']['project']['projectUserMembershipBulk']
        self.assertMatchSnapshot(response, 'try 1')
        # ----------------- Another try
        minput['projectMembership'].pop(1)
        minput['projectMembership'].extend([
            # Invalid (changing member)
            dict(
                member=member_user6.pk,
                clientId="member-user-2",
                role=self.project_role_clairvoyant_one.pk,
                id=membership2.pk,
            ),
            dict(
                member=member_user2.pk,
                clientId="member-user-2",
                role=self.project_role_admin.pk,
                id=membership2.pk,
            ),
        ])
        response = _query_check()['data']['project']['projectUserMembershipBulk']
        self.assertMatchSnapshot(response, 'try 2')

    def test_user_membership_using_clairvoyan_one_bulk(self):
        self._user_membership_bulk(self.project_role_clairvoyant_one)

    def test_user_membership_admin_bulk(self):
        self._user_membership_bulk(self.project_role_admin)

    def _user_group_membership_bulk(self, user_role):
        query = '''
          mutation MyMutation(
              $id: ID!,
              $projectMembership: [BulkProjectUserGroupMembershipInputType!],
              $projectMembershipDelete: [ID!]!
          ) {
          project(id: $id) {
            id
            title
            projectUserGroupMembershipBulk(items: $projectMembership, deleteIds: $projectMembershipDelete) {
              errors
              result {
                id
                clientId
                joinedAt
                addedBy {
                  id
                  displayName
                }
                role {
                  id
                  title
                }
                usergroup {
                  id
                  title
                }
                badges
              }
              deletedResult {
                id
                clientId
                joinedAt
                usergroup {
                  id
                  title
                }
                role {
                  id
                  title
                  level
                }
                addedBy {
                  id
                  displayName
                }
                badges
              }
            }
          }
        }
        '''
        project = ProjectFactory.create()

        def _add_member(usergroup, role=None, badges=[]):
            return ProjectUserGroupMembership.objects.create(
                project=project,
                usergroup=usergroup,
                role_id=(role and role.id) or get_default_role_id(),
                badges=badges,
            )

        user = UserFactory.create()
        user_group = UserGroupFactory.create()
        user_group.members.add(user)

        (
            member_user_group0,
            member_user_group1,
            member_user_group2,
            member_user_group3,
            member_user_group4,
            member_user_group5,
            member_user_group6
        ) = UserGroupFactory.create_batch(7)

        membership1 = _add_member(member_user_group1, badges=[ProjectMembership.BadgeType.QA])
        membership2 = _add_member(member_user_group2)
        _add_member(member_user_group5)
        another_clairvoyant_user_group = _add_member(member_user_group0, role=self.project_role_clairvoyant_one)
        user_group_membership = _add_member(user_group, role=user_role)

        minput = dict(
            projectMembershipDelete=[
                str(membership1.pk),  # This will be only on try 1
                # This shouldn't be on any response (requester + creater)
                str(user_group_membership.pk),
                str(another_clairvoyant_user_group.pk),
            ],
            projectMembership=[
                # Try updating membership (Valid on try 1, invalid on try 2)
                dict(
                    usergroup=member_user_group2.pk,
                    clientId="member-user-2",
                    role=self.project_role_clairvoyant_one.pk,
                    id=membership2.pk,
                    badges=[self.genum(ProjectMembership.BadgeType.QA)],
                ),
                # Try adding already existing member
                dict(
                    usergroup=member_user_group5.pk,
                    clientId="member-user-5",
                    role=self.project_role_analyst.pk,
                ),
                # Try adding new member (Valid on try 1, invalid on try 2)
                dict(
                    usergroup=member_user_group3.pk,
                    clientId="member-user-3",
                    role=self.project_role_analyst.pk,
                ),
                # Try adding new member (without giving role) -> this should use default role
                # Valid on try 1, invalid on try 2
                dict(
                    usergroup=member_user_group4.pk,
                    clientId="member-user-4",
                ),
            ],
        )

        def _query_check(**kwargs):
            return self.query_check(
                query,
                mnested=['project'],
                variables={'id': project.id, **minput},
                **kwargs,
            )
        # ---------- With login (with higher permission)
        self.force_login(user)
        # ----------------- Some Invalid input
        response = _query_check()['data']['project']['projectUserGroupMembershipBulk']
        self.assertMatchSnapshot(response, 'try 1')
        # ----------------- Another try
        minput['projectMembership'].pop(1)
        minput['projectMembership'].extend([
            # Invalid (changing member)
            dict(
                usergroup=member_user_group6.pk,
                clientId="member-user-2",
                role=self.project_role_clairvoyant_one.pk,
                id=membership2.pk,
            ),
            dict(
                usergroup=member_user_group2.pk,
                clientId="member-user-2",
                role=self.project_role_admin.pk,
                id=membership2.pk,
            ),
        ])
        response = _query_check()['data']['project']['projectUserGroupMembershipBulk']
        self.assertMatchSnapshot(response, 'try 2')

    def test_user_group_membership_using_clairvoyan_one_bulk(self):
        self._user_group_membership_bulk(self.project_role_clairvoyant_one)

    def test_user_group_membership_admin_bulk(self):
        self._user_group_membership_bulk(self.project_role_admin)
