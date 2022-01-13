from deep.tests import TestCase
from project.models import (
    Project,
    ProjectMembership,
    ProjectJoinRequest,
)
from user.models import (
    User,
    EmailDomain,
    Feature,
)
from user.notifications import Notification


class UserApiTests(TestCase):
    def test_active_project(self):
        # Create a project with self.user as member
        # and test setting it as active project through the API
        project = Project.objects.create(title='Test')
        ProjectMembership.objects.create(project=project,
                                         member=self.user,
                                         role=self.admin_role)

        url = '/api/v1/users/{}/'.format(self.user.pk)
        data = {
            'last_active_project': project.id,
        }

        self.authenticate()
        response = self.client.patch(url, data)
        self.assert_405(response)

        # Get latest user info from db and check if last active
        # project is set properly
        self.user = User.objects.get(id=self.user.id)
        self.assertNotEqual(self.user.profile.last_active_project, project)

    def test_patch_user(self):
        # TODO: Add old_password to change password
        url = '/api/v1/users/{}/'.format(self.user.pk)
        data = {
            'password': 'newpassword',
            'receive_email': False,
        }

        self.authenticate()
        response = self.client.patch(url, data)
        self.assert_405(response)

    def test_authentication_in_users_instance(self):
        user = self.create(User, first_name='hello', last_name='bye')

        url = f'/api/v1/users/{user.id}/'

        # try to get with no authentication
        response = self.client.get(url)
        self.assert_401(response)

        # now authenticate
        self.authenticate(user)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data['first_name'], user.first_name)

    def test_get_me(self):
        url = '/api/v1/users/me/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['username'], self.user.username)

    def test_search_user_without_exclude(self):
        project = self.create(Project)
        user1 = self.create(User, first_name='search', last_name='user')
        user2 = self.create(User, first_name='user', last_name='search')
        user3 = self.create(User, first_name='my search', last_name='user')
        user4 = self.create(User, email='search@toggle.com')
        # Create another non matching user, just to make sure it doesn't appear
        # in result
        self.create(
            User,
            first_name='abc',
            last_name='xyz',
            email='something@toggle.com'
        )
        # Add members to project
        project.add_member(user1)

        # Search query is 'search'
        url = '/api/v1/users/?search=search'
        self.authenticate()

        response = self.client.get(url)
        self.assert_200(response)

        data = response.json()

        assert data['count'] == 4
        # user1 is most matching and user4 is the least matching,
        # user5 does not match
        assert data['results'][0]['id'] == user1.id
        assert data['results'][1]['id'] == user3.id
        assert data['results'][2]['id'] == user2.id
        assert data['results'][3]['id'] == user4.id

    def test_search_user_with_exclude(self):
        project = self.create(Project)
        user1 = self.create(User, first_name='search', last_name='user')
        user2 = self.create(User, first_name='user', last_name='search')
        user3 = self.create(User, first_name='my search', last_name='user')
        # Add members to project
        project.add_member(user1)

        # Search query is 'search'
        url = '/api/v1/users/?search=search&members_exclude_project=' \
            + str(project.id)
        self.authenticate()

        response = self.client.get(url)
        self.assert_200(response)

        data = response.json()

        assert data['count'] == 2, "user 1 is in the project, so one less"
        # user3 is most matching and user2 is the least matching
        assert data['results'][0]['id'] == user3.id
        assert data['results'][1]['id'] == user2.id

    def test_notifications(self):
        test_project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)

        request = ProjectJoinRequest.objects.create(
            project=test_project,
            requested_by=test_user,
            role=self.admin_role
        )

        url = '/api/v1/users/me/notifications/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 1)
        result = response.data['results'][0]
        self.assertEqual(result['type'], Notification.PROJECT_JOIN_REQUEST)
        self.assertEqual(result['details']['id'], request.id)

    def test_user_preference_feature_access(self):
        user_fhx = self.create(User, email='fhx@togglecorp.com')
        user_az273 = self.create(User, email='az273@tc.com')
        user_dummy = self.create(User, email='dummy@test.com')

        test_domain = self.create(EmailDomain, title='Togglecorp', domain_name='togglecorp.com')
        self.create(Feature, feature_type=Feature.FeatureType.GENERAL_ACCESS,
                    key=Feature.FeatureKey.PRIVATE_PROJECT, title='Private project',
                    email_domains=[test_domain], users=[user_dummy])

        self.authenticate(user_fhx)
        response = self.client.get('/api/v1/users/me/preferences/')
        self.assertEqual(len(response.data['accessible_features']), 1)

        self.authenticate(user_az273)
        response = self.client.get('/api/v1/users/me/preferences/')
        self.assertEqual(len(response.data['accessible_features']), 0)

        self.authenticate(user_dummy)
        response = self.client.get('/api/v1/users/me/preferences/')
        self.assertEqual(len(response.data['accessible_features']), 1)

    def test_user_preference_feature_available_for_all(self):
        user_fhx = self.create(User, email='fhx@togglecorp.com')

        feature = self.create(Feature, feature_type=Feature.FeatureType.GENERAL_ACCESS,
                              key=Feature.FeatureKey.PRIVATE_PROJECT, title='Private project',
                              email_domains=[], users=[], is_available_for_all=False)

        self.authenticate(user_fhx)
        response = self.client.get('/api/v1/users/me/preferences/')
        self.assertEqual(len(response.data['accessible_features']), 0)

        feature.is_available_for_all = True
        feature.save()

        self.authenticate(user_fhx)
        response = self.client.get('/api/v1/users/me/preferences/')
        self.assertEqual(len(response.data['accessible_features']), 1)

    def test_password_change(self):
        self.user_password = 'joHnDave!@#123'
        user = User.objects.create_user(
            username='ram@dave.com',
            first_name='Ram',
            last_name='Dave',
            password=self.user_password,
            email='ram@dave.com',
        )
        new_pass = "nepal!@#RRFASF"
        data = {
            "old_password": self.user_password,
            "new_password": new_pass
        }
        url = '/api/v1/users/me/change-password/'
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_200(response)

        user.refresh_from_db()
        assert user.check_password(data['new_password'])

        # now try with posting  diferent `new_password` that doesnot follow django password validation
        data = {
            "old_password": new_pass,  # since password is already changed in the database level
            "new_password": "nepa"
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_400(response)

        # now try with posting different `old_password`
        data = {
            "old_password": "hahahmeme",
            "new_password": "nepa"
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_400(response)

        # test for other method
        self.authenticate(user)
        response = self.client.get(url)
        self.assert_405(response)
