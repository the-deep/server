from rest_framework import status
from rest_framework.test import APITestCase
from user.tests.test_apis import AuthMixin
from project.models import Project, ProjectMembership


class ProjectMixin():
    """
    Project related methods
    """
    def create_or_get_project(self):
        """
        Create new or return recent project
        """
        project = Project.objects.first()
        if not project:
            project = Project.objects.create(
                title='Test project',
            )

            if self.user:
                ProjectMembership.objects.create(
                    member=self.user,
                    project=project,
                    role='admin',
                )

        return project


class ProjectApiTest(AuthMixin, ProjectMixin, APITestCase):
    """
    Project Tests
    """
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

    def test_create_project(self):
        """
        Create Project Test
        """
        url = '/api/v1/projects/'
        data = {
            'title': 'Test project',
            'data': {'testKey': 'testValue'},
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(response.data['title'], data['title'])

        # Test that the user has been made admin
        self.assertEqual(len(response.data['members']), 1)
        self.assertEqual(response.data['members'][0], self.user.pk)

        self.assertEqual(len(response.data['memberships']), 1)

        membership = ProjectMembership.objects.get(
            pk=response.data['memberships'][0])
        self.assertEqual(membership.member.pk, self.user.pk)
        self.assertEqual(membership.role, 'admin')

    def test_add_member(self):
        """
        Add Project Members
        """
        project = self.create_or_get_project()
        test_user = self.create_new_user()

        url = '/api/v1/project-memberships/'
        data = {
            'member': test_user.pk,
            'project': project.pk,
            'role': 'normal',
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], data['role'])
        self.assertEqual(response.data['member'], data['member'])
        self.assertEqual(response.data['project'], data['project'])


# EOF
