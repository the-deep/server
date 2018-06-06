from deep.tests import TestCase
from project.models import (
    Project,
    ProjectMembership,
    ProjectJoinRequest,
)
from user.models import User
from user.notifications import Notification


class UserApiTests(TestCase):
    def test_create_user(self):
        user_count = User.objects.count()

        url = '/api/v1/users/'
        data = {
            'username': 'bibekdahal.bd16@gmail.com',
            'email': 'bibekdahal.bd16@gmail.com',
            'first_name': 'Bibek',
            'last_name': 'Dahal',
            'organization': 'Togglecorp',
            'password': 'admin123',
            'display_picture': None,
            'recaptcha_response': 'TEST',
        }

        # TODO: Test display picture api

        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertEqual(response.data['username'], data['username'])

    def test_active_project(self):
        # Create a project with self.user as member
        # and test setting it as active project through the API
        project = Project.objects.create(title='Test')
        ProjectMembership.objects.create(project=project,
                                         member=self.user)

        url = '/api/v1/users/{}/'.format(self.user.pk)
        data = {
            'last_active_project': project.id,
        }

        self.authenticate()
        response = self.client.patch(url, data)
        self.assert_200(response)

        # Get latest user info from db and check if last active
        # project is set properly
        self.user = User.objects.get(id=self.user.id)
        self.assertEqual(self.user.profile.last_active_project, project)

    def test_patch_user(self):
        # TODO: Add old_password to change password
        url = '/api/v1/users/{}/'.format(self.user.pk)
        data = {
            'password': 'newpassword',
        }

        self.authenticate()
        response = self.client.patch(url, data)
        self.assert_200(response)

    def test_get_me(self):
        url = '/api/v1/users/me/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['username'], self.user.username)

    def test_notifications(self):
        test_project = self.create(Project)
        test_user = self.create(User)

        request = ProjectJoinRequest.objects.create(
            project=test_project,
            requested_by=test_user,
        )

        url = '/api/v1/users/me/notifications/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 1)
        result = response.data['results'][0]
        self.assertEqual(result['type'], Notification.PROJECT_JOIN_REQUEST)
        self.assertEqual(result['details']['id'], request.id)
