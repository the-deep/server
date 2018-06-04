from user.models import User
from deep.tests import TestCase
from project.models import (
    Project,
    ProjectMembership,
    ProjectJoinRequest,
)


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

        self.assertEqual(response.data['project'], project.id)
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
