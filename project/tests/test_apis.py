from user.models import User
from deep.tests import TestCase
from entry.models import Lead, Entry
from project.models import (
    Project,
    ProjectMembership,
    ProjectJoinRequest,
    ProjectStatus,
    ProjectStatusCondition,
    ProjectUserGroupMembership,
)

from user_group.models import UserGroup

from django.utils import timezone
from datetime import timedelta


# TODO Document properly some of the following complex tests


class ProjectApiTest(TestCase):

    def setUp(self):
        super().setUp()
        # create some users
        self.user1 = self.create(User)
        self.user2 = self.create(User)
        self.user3 = self.create(User)
        # and some user groups
        self.ug1 = self.create(UserGroup, role='admin')
        self.ug1.add_member(self.user1)
        self.ug1.add_member(self.user2)
        self.ug2 = self.create(UserGroup, role='admin')
        self.ug2.add_member(self.user2)
        self.ug2.add_member(self.user3)

    def test_create_project(self):
        project_count = Project.objects.count()

        url = '/api/v1/projects/'
        data = {
            'title': 'Test project',
            'data': {'testKey': 'testValue'},
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Project.objects.count(), project_count + 1)
        self.assertEqual(response.data['title'], data['title'])

        # Test that the user has been made admin
        self.assertEqual(len(response.data['memberships']), 1)
        self.assertEqual(response.data['memberships'][0]['member'],
                         self.user.pk)

        # assert single membership
        self.assertEqual(len(response.data['memberships']), 1)
        membership = ProjectMembership.objects.get(
            pk=response.data['memberships'][0]['id'])
        self.assertEqual(membership.member.pk, self.user.pk)
        self.assertEqual(membership.role, self.admin_role)

    def test_update_project_add_ug(self):
        project = self.create(
            Project,
            user_groups=[],
            title='TestProject',
            role=self.admin_role
        )

        memberships = ProjectMembership.objects.filter(project=project)
        initial_member_count = memberships.count()

        url = '/api/v1/project-usergroups/'
        data = {
            'project': project.id,
            'usergroup': self.ug1.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        assert response.status_code == 201

        final_memberships = ProjectMembership.objects.filter(project=project)
        final_member_count = final_memberships.count()
        # now check for members
        self.assertEqual(
            initial_member_count + self.ug1.members.all().count() - 1,
            # -1 because usergroup admin and project admin is common
            final_member_count
        )

    def test_update_project_remove_ug(self):
        project = self.create(
            Project,
            title='TestProject',
            user_groups=[],
            role=self.admin_role
        )
        # Add usergroups
        ProjectUserGroupMembership.objects.create(
            usergroup=self.ug1,
            project=project
        )
        project_ug2 = ProjectUserGroupMembership.objects.create(
            usergroup=self.ug2,
            project=project
        )

        initial_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()

        # We keep just ug1, and remove ug2
        url = '/api/v1/project-usergroups/{}/'.format(project_ug2.id)

        self.authenticate()
        response = self.client.delete(url)
        self.assert_204(response)

        final_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()

        # now check for members
        self.assertEqual(
            # Subtract all members from second group except
            # the two users that are common in both user groups
            initial_member_count - self.ug2.members.all().count() + 2,
            final_member_count
        )

    def test_add_user_to_usergroup(self):
        project = self.create(
            Project,
            title='TestProject',
            user_groups=[],
            role=self.admin_role
        )
        # Add usergroups
        project_ug1 = ProjectUserGroupMembership.objects.create(
            usergroup=self.ug1,
            project=project
        )
        initial_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()
        # Create a new user and add it to project_ug1
        newUser = self.create(User)

        from user_group.models import GroupMembership
        GroupMembership.objects.create(
            member=newUser,
            group=project_ug1.usergroup
        )
        final_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()
        self.assertEqual(initial_member_count + 1, final_member_count)

    def test_remove_user_in_only_one_usergroup(self):
        project = self.create(
            Project,
            title='TestProject',
            user_groups=[],
            role=self.admin_role
        )

        # Add usergroups
        project_ug1 = ProjectUserGroupMembership.objects.create(
            usergroup=self.ug1,
            project=project
        )

        initial_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()

        from user_group.models import GroupMembership

        GroupMembership.objects.filter(
            member=self.user1,  # user1 belongs to ug1
            group=project_ug1.usergroup
        ).delete()

        final_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()
        self.assertEqual(initial_member_count - 1, final_member_count)

    def test_remove_user_in_only_multiple_usergroups(self):
        project = self.create(
            Project,
            title='TestProject',
            user_groups=[],
            role=self.admin_role
        )

        # Add usergroups
        project_ug1 = ProjectUserGroupMembership.objects.create(
            usergroup=self.ug1,
            project=project
        )
        ProjectUserGroupMembership.objects.create(
            usergroup=self.ug2,
            project=project
        )

        initial_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()

        from user_group.models import GroupMembership

        GroupMembership.objects.filter(
            member=self.user2,  # user1 belongs to ug1 and ug2
            group=project_ug1.usergroup
        ).delete()

        final_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()
        # Should be no change in membeship as user2 is member from ug2 as well
        self.assertEqual(initial_member_count, final_member_count)

    def test_member_of(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)

        url = '/api/v1/projects/member-of/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], project.id)

        url = '/api/v1/projects/member-of/?user={}'.format(test_user.id)

        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 0)

    def test_add_member(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)

        url = '/api/v1/project-memberships/'
        data = {
            'member': test_user.pk,
            'project': project.pk,
            'role': self.normal_role.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(response.data['role'], data['role'])
        self.assertEqual(response.data['member'], data['member'])
        self.assertEqual(response.data['project'], data['project'])

    def test_add_member_unexistent_role(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)

        url = '/api/v1/project-memberships/'
        data = {
            'member': test_user.pk,
            'project': project.pk,
            'role': 9999
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_400(response)
        assert 'errors' in response.data

    def test_options(self):
        url = '/api/v1/project-options/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

    def test_join_request(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)

        url = '/api/v1/projects/{}/join/'.format(project.id)

        self.authenticate(test_user)
        response = self.client.post(url)
        self.assert_201(response)

        self.assertEqual(response.data['project']['id'], project.id)
        self.assertEqual(response.data['requested_by']['id'], test_user.id)

    def test_accept_request(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=test_user,
            role=self.admin_role
        )

        url = '/api/v1/projects/{}/requests/{}/accept/'.format(
            project.id,
            request.id,
        )

        self.authenticate()
        response = self.client.post(url)
        self.assert_200(response)

        self.assertEqual(response.data['responded_by']['id'], self.user.id)
        self.assertEqual(response.data['status'], 'accepted')
        membership = ProjectMembership.objects.filter(
            project=project,
            member=test_user,
            role=self.normal_role,
        )
        self.assertEqual(membership.count(), 1)

    def test_reject_request(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=test_user,
            role=self.admin_role
        )

        url = '/api/v1/projects/{}/requests/{}/reject/'.format(
            project.id,
            request.id,
        )

        self.authenticate()
        response = self.client.post(url)
        self.assert_200(response)

        self.assertEqual(response.data['responded_by']['id'], self.user.id)
        self.assertEqual(response.data['status'], 'rejected')
        membership = ProjectMembership.objects.filter(
            project=project,
            member=test_user,
            role=self.normal_role
        )
        self.assertEqual(membership.count(), 0)

    def test_cancel_request(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=test_user,
            role=self.admin_role
        )

        url = '/api/v1/projects/{}/join/cancel/'.format(project.id)

        self.authenticate(test_user)
        response = self.client.post(url)
        self.assert_204(response)

        request = ProjectJoinRequest.objects.filter(id=request.id)
        self.assertEqual(request.count(), 0)

    def test_list_request(self):
        project = self.create(Project, role=self.admin_role)
        self.create(ProjectJoinRequest, project=project)
        self.create(ProjectJoinRequest, project=project)
        self.create(ProjectJoinRequest, project=project)

        url = '/api/v1/projects/{}/requests/'.format(project.id)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['count'], 3)

    def test_delete_project_admin(self):
        project = self.create(Project, role=self.admin_role)
        url = '/api/v1/projects/{}/'.format(project.id)
        self.authenticate()
        response = self.client.delete(url)
        self.assert_204(response)

    def test_delete_project_normal(self):
        project = self.create(Project, role=self.admin_role)
        user = self.create(User)

        project.add_member(user)

        url = '/api/v1/projects/{}/'.format(project.id)
        self.authenticate(user)

        response = self.client.delete(url)
        self.assert_403(response)

    def test_can_modify(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        project.add_member(test_user)
        assert project.can_modify(self.user)
        assert not project.can_modify(test_user)

    def test_auto_accept(self):
        # When a project member is added, if there is a pending
        # request for that user, auto accept that request
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=test_user,
            role=self.admin_role
        )
        project.add_member(test_user, self.normal_role, self.user)

        request = ProjectJoinRequest.objects.get(id=request.id)
        self.assertEqual(request.status, 'accepted')
        self.assertEqual(request.responded_by, self.user)

    def _test_status_filter(self, and_conditions):
        status = self.create(ProjectStatus, and_conditions=and_conditions)
        self.create(
            ProjectStatusCondition,
            project_status=status,
            condition_type=ProjectStatusCondition.NO_LEADS_CREATED,
            days=5,
        )
        self.create(
            ProjectStatusCondition,
            project_status=status,
            condition_type=ProjectStatusCondition.NO_ENTRIES_CREATED,
            days=5,
        )
        old_date = timezone.now() - timedelta(days=8)

        # One with old lead
        project1 = self.create(Project, role=self.admin_role)
        lead = self.create(Lead, project=project1)
        Lead.objects.filter(pk=lead.pk).update(created_at=old_date)
        Lead.objects.get(pk=lead.pk).save()

        # One with latest lead
        project2 = self.create(Project, role=self.admin_role)
        self.create(Lead, project=project2)

        # One empty
        self.create(Project, role=self.admin_role)

        # One with latest lead but expired entry
        project4 = self.create(Project, role=self.admin_role)
        lead = self.create(Lead, project=project4)
        entry = self.create(Entry, lead=lead)
        Entry.objects.filter(pk=entry.pk).update(created_at=old_date)
        Lead.objects.get(pk=lead.pk).save()

        # One with expired lead and expired entry
        project5 = self.create(Project, role=self.admin_role)
        lead = self.create(Lead, project=project5)
        entry = self.create(Entry, lead=lead)
        Lead.objects.filter(pk=lead.pk).update(created_at=old_date)
        Entry.objects.filter(pk=entry.pk).update(created_at=old_date)
        Lead.objects.get(pk=lead.pk).save()

        url = '/api/v1/projects/?status={}'.format(status.id)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        expected = [
            project1.id,
            project5.id,
        ] if and_conditions else [
            project1.id,
            project2.id,
            project4.id,
            project5.id,
        ]
        obtained = [r['id'] for r in response.data['results']]

        self.assertEqual(response.data['count'], len(expected))
        self.assertTrue(sorted(expected) == sorted(obtained))

    def test_status_filter_or_conditions(self):
        self._test_status_filter(False)

    def test_status_filter_and_conditions(self):
        self._test_status_filter(True)

    def test_involvment_filter(self):
        project1 = self.create(Project, role=self.admin_role)
        project2 = self.create(Project, role=self.admin_role)
        project3 = self.create(Project, role=self.admin_role)

        test_user = self.create(User)
        project1.add_member(test_user, role=self.normal_role)
        project2.add_member(test_user, role=self.normal_role)

        url = '/api/v1/projects/?involvement=my_projects'

        self.authenticate(test_user)
        response = self.client.get(url)
        self.assert_200(response)

        expected = [
            project1.id,
            project2.id
        ]
        obtained = [r['id'] for r in response.data['results']]

        self.assertEqual(response.data['count'], len(expected))
        self.assertTrue(sorted(expected) == sorted(obtained))

        url = '/api/v1/projects/?involvement=not_my_projects'

        self.authenticate(test_user)
        response = self.client.get(url)
        self.assert_200(response)

        expected = [
            project3.id,
        ]
        obtained = [r['id'] for r in response.data['results']]

        self.assertEqual(response.data['count'], len(expected))
        self.assertTrue(sorted(expected) == sorted(obtained))
