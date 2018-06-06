from user.models import User
from deep.tests import TestCase
from entry.models import Lead, Entry
from project.models import (
    Project,
    ProjectMembership,
    ProjectJoinRequest,
    ProjectStatus,
    ProjectStatusCondition,
)

from django.utils import timezone
from datetime import timedelta


# TODO Document properly some of the following complex tests


class ProjectApiTest(TestCase):
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

        membership = ProjectMembership.objects.get(
            pk=response.data['memberships'][0]['id'])
        self.assertEqual(membership.member.pk, self.user.pk)
        self.assertEqual(membership.role, 'admin')

    def test_member_of(self):
        project = self.create(Project)
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
        project = self.create(Project)
        test_user = self.create(User)

        url = '/api/v1/project-memberships/'
        data = {
            'member': test_user.pk,
            'project': project.pk,
            'role': 'normal',
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(response.data['role'], data['role'])
        self.assertEqual(response.data['member'], data['member'])
        self.assertEqual(response.data['project'], data['project'])

    def test_options(self):
        url = '/api/v1/project-options/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

    def test_join_request(self):
        project = self.create(Project)
        test_user = self.create(User)

        url = '/api/v1/projects/{}/join/'.format(project.id)

        self.authenticate(test_user)
        response = self.client.post(url)
        self.assert_201(response)

        self.assertEqual(response.data['project']['id'], project.id)
        self.assertEqual(response.data['requested_by']['id'], test_user.id)

    def test_accept_request(self):
        project = self.create(Project)
        test_user = self.create(User)
        request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=test_user
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
            role='normal',
        )
        self.assertEqual(membership.count(), 1)

    def test_reject_request(self):
        project = self.create(Project)
        test_user = self.create(User)
        request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=test_user
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
            role='normal',
        )
        self.assertEqual(membership.count(), 0)

    def test_list_request(self):
        project = self.create(Project)
        self.create(ProjectJoinRequest, project=project)
        self.create(ProjectJoinRequest, project=project)
        self.create(ProjectJoinRequest, project=project)

        url = '/api/v1/projects/{}/requests/'.format(project.id)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['count'], 3)

    def test_auto_accept(self):
        # When a project member is added, if there is a pending
        # request for that user, auto accept that request
        project = self.create(Project)
        test_user = self.create(User)
        request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=test_user,
        )
        project.add_member(test_user, 'normal', self.user)

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
        project1 = self.create(Project)
        lead = self.create(Lead, project=project1)
        Lead.objects.filter(pk=lead.pk).update(created_at=old_date)

        # One with latest lead
        project2 = self.create(Project)
        self.create(Lead, project=project2)

        # One empty
        self.create(Project)

        # One with latest lead but expired entry
        project4 = self.create(Project)
        lead = self.create(Lead, project=project4)
        entry = self.create(Entry, lead=lead)
        Entry.objects.filter(pk=entry.pk).update(created_at=old_date)

        # One with expired lead and expired entry
        project5 = self.create(Project)
        lead = self.create(Lead, project=project5)
        entry = self.create(Entry, lead=lead)
        Lead.objects.filter(pk=lead.pk).update(created_at=old_date)
        Entry.objects.filter(pk=entry.pk).update(created_at=old_date)

        url = '/api/v1/projects/?status={}'.format(status.id)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        expected = [
            project5.id,
        ] if and_conditions else [
            project1.id,
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
        project1 = self.create(Project)
        project2 = self.create(Project)
        project3 = self.create(Project)

        test_user = self.create(User)
        project1.add_member(test_user)
        project2.add_member(test_user)

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
