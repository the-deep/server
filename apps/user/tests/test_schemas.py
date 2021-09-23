from unittest import mock
from django.conf import settings
from django.utils import timezone

from utils.graphene.tests import GraphQLTestCase

from gallery.factories import FileFactory
from project.factories import ProjectFactory
from user.models import User, Feature
from user.factories import UserFactory, FeatureFactory
from user.utils import (
    send_password_changed_notification,
    send_password_reset,
    send_account_activation,
)
from utils.hid.tests.test_hid import (
    HIDIntegrationTest,
    HID_EMAIL
)


class TestUserSchema(GraphQLTestCase):
    def setUp(self):
        # This is used in 2 test
        self.login_mutation = '''
            mutation Mutation($input: LoginInputType!) {
              login(data: $input) {
                ok
                captchaRequired
                result {
                  id
                  displayName
                  email
                  lastLogin
                }
              }
            }
        '''
        super().setUp()

    def test_login(self):
        # Try with random user
        minput = dict(email='xyz@xyz.com', password='pasword-xyz')
        self.query_check(self.login_mutation, minput=minput, okay=False)

        # Try with real user
        user = UserFactory.create(email=minput['email'])
        minput = dict(email=user.email, password=user.password_text)
        content = self.query_check(self.login_mutation, minput=minput, okay=True)
        # FIXME: Maybe ['id'] should be string?
        self.assertEqual(content['data']['login']['result']['id'], str(user.id), content)
        self.assertEqual(content['data']['login']['result']['email'], user.email, content)

    @mock.patch('jwt_auth.captcha.requests')
    @mock.patch('user.serializers.send_account_activation', side_effect=send_account_activation)
    def test_login_captcha(self, send_account_activation_mock, captch_requests_mock):
        """
        - Test captcha response.
        - Test account block behaviour
        """
        def _invalid_login():
            content = self.query_check(
                self.login_mutation,
                minput=dict(
                    email=user.email,
                    password='wrong-password',
                    captcha='captcha',
                ),
                okay=False,
            )
            user.refresh_from_db()
            return content

        def _valid_login(okay):
            return self.query_check(
                self.login_mutation,
                minput=dict(
                    email=user.email,
                    password=user.password_text,
                    captcha='captcha',
                ),
                okay=okay,
            )

        captch_requests_mock.post.return_value.json.return_value = {'success': False}
        user = UserFactory.create()
        # For MAX_LOGIN_ATTEMPTS_FOR_CAPTCHA count failed login attempt
        for attempt in range(1, 5):
            content = _invalid_login()
            if attempt < settings.MAX_LOGIN_ATTEMPTS_FOR_CAPTCHA:
                self.assertEqual(user.profile.login_attempts, attempt, content)
            else:
                # Count stoped (when valid captch is not provided)
                self.assertEqual(user.profile.login_attempts, settings.MAX_LOGIN_ATTEMPTS_FOR_CAPTCHA, content)
        # After MAX_LOGIN_ATTEMPTS_FOR_CAPTCHA count failed captcha is required
        captch_requests_mock.post.return_value.json.return_value = {'success': True}
        for attempt in range(
            settings.MAX_LOGIN_ATTEMPTS_FOR_CAPTCHA + 1,
            settings.MAX_LOGIN_ATTEMPTS + 2,
        ):
            content = _invalid_login()
            if user.profile.login_attempts > settings.MAX_LOGIN_ATTEMPTS:
                # Email is sent
                send_account_activation_mock.assert_called_once_with(user)
                # Not accepting any new attempt
                self.assertEqual(user.profile.login_attempts, settings.MAX_LOGIN_ATTEMPTS + 1, content)
            else:
                send_account_activation_mock.assert_not_called()
                self.assertEqual(user.profile.login_attempts, attempt, content)
            # Count all failed count (when valid captch is provided)

        # Still can't login (with right password).
        captch_requests_mock.post.return_value.json.return_value = {'success': True}
        content = _valid_login(okay=False)

        # mock activation link logic
        user.profile.login_attempts = 0
        user.profile.save(update_fields=['login_attempts'])

        content = _valid_login(okay=True)

    @mock.patch('utils.hid.hid.requests')
    def test_login_with_hid(self, mock_requests):
        query = '''
            mutation Mutation($input: HIDLoginInputType!) {
                loginWithHid(data: $input) {
                    ok
                    errors
                    result {
                        id
                        displayName
                        email
                        lastLogin
                    }
                }
            }
        '''
        mock_return_value = HIDIntegrationTest()._setup_mock_hid_requests(mock_requests)
        minput = dict(accessToken='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        content = self.query_check(query, minput=minput, okay=True)
        self.assertEqual(content['data']['loginWithHid']['result']['email'], HID_EMAIL)

        # let the response be `400` and look for the error
        mock_return_value.status_code = 400
        content = self.query_check(query, minput=minput, assert_for_error=True)
        mock_return_value.status_code = 200

        # pass not verified email
        mock_return_value.json.return_value['email_verified'] = False
        self.query_check(query, minput=minput, assert_for_error=True)
        mock_return_value.json.return_value['email_verified'] = True

    @mock.patch('jwt_auth.captcha.requests')
    @mock.patch('user.serializers.send_password_reset', side_effect=send_password_reset)
    def test_register(self, send_password_reset_mock, captch_requests_mock):
        query = '''
            mutation Mutation($input: RegisterInputType!) {
              register(data: $input) {
                ok
                captchaRequired
                errors
              }
            }
        '''
        # input without email
        minput = dict(
            email='invalid-email',
            firstName='john',
            lastName='cena',
            organization='the-deep',
            captcha='captcha',
        )

        # With invalid captcha
        captch_requests_mock.post.return_value.json.return_value = {'success': False}
        content = self.query_check(query, minput=minput, okay=False)

        # With valid captcha now
        captch_requests_mock.post.return_value.json.return_value = {'success': True}
        # With invalid email
        content = self.query_check(query, minput=minput, okay=False)
        self.assertEqual(len(content['data']['register']['errors']), 1, content)

        # With valid input
        minput['email'] = 'john@cena.com'
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(query, minput=minput, okay=True)
        # Make sure password reset message is send
        user = User.objects.get(email=minput['email'])
        send_password_reset_mock.assert_called_once_with(user=user, welcome=True)

    def test_logout(self):
        query = '''
            query Query {
              me {
                id
                email
              }
            }
        '''
        logout_mutation = '''
            mutation Mutation {
              logout {
                ok
              }
            }
        '''
        user = UserFactory.create()
        # # Without Login session
        content = self.query_check(query, assert_for_error=True)
        # # Login
        self.force_login(user)
        # Query Me (Success)
        content = self.query_check(query)
        self.assertEqual(content['data']['me']['id'], str(user.id), content)
        self.assertEqual(content['data']['me']['email'], user.email, content)
        # # Logout
        self.query_check(logout_mutation, okay=True)
        # Query Me (with error again)
        content = self.query_check(query, assert_for_error=True)

    @mock.patch('jwt_auth.captcha.requests')
    @mock.patch('user.serializers.send_password_reset', side_effect=send_password_reset)
    def test_password_reset(self, send_password_reset_mock, captch_requests_mock):
        query = '''
            mutation Mutation($input: ResetPasswordInputType!) {
              resetPassword(data: $input) {
                ok
                captchaRequired
                errors
              }
            }
        '''
        # input without email
        minput = dict(
            email='invalid-email',
            captcha='captcha',
        )

        # With invalid captcha
        captch_requests_mock.post.return_value.json.return_value = {'success': False}
        content = self.query_check(query, minput=minput, okay=False)

        # With valid captcha now
        captch_requests_mock.post.return_value.json.return_value = {'success': True}
        # With invalid email
        content = self.query_check(query, minput=minput, okay=False)
        self.assertEqual(len(content['data']['resetPassword']['errors']), 1, content)

        # With unknown user email
        minput['email'] = 'john@cena.com'
        content = self.query_check(query, minput=minput, okay=False)
        self.assertEqual(len(content['data']['resetPassword']['errors']), 1, content)

        # With known user email
        UserFactory.create(email=minput['email'])
        content = self.query_check(query, minput=minput, okay=True)
        # Make sure password reset message is send
        user = User.objects.get(email=minput['email'])
        send_password_reset_mock.assert_called_once_with(user=user)

    @mock.patch(
        'user.serializers.send_password_changed_notification.delay',
        side_effect=send_password_changed_notification.delay,
    )
    def test_password_change(self, send_password_changed_notification_mock):
        query = '''
            mutation Mutation($input: PasswordChangeInputType!) {
              changePassword(data: $input) {
                ok
                errors
              }
            }
        '''
        # input without email
        minput = dict(oldPassword='', newPassword='new-password-123')
        # Without authentication --
        content = self.query_check(query, minput=minput, assert_for_error=True)
        # With authentication
        user = UserFactory.create()
        self.force_login(user)
        # With invalid old password --
        content = self.query_check(query, minput=minput, okay=False)
        self.assertEqual(len(content['data']['changePassword']['errors']), 1, content)
        # With valid password --
        minput['oldPassword'] = user.password_text
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(query, minput=minput, okay=True)
        # Make sure password reset message is send
        send_password_changed_notification_mock.assert_called_once()
        send_password_changed_notification_mock.assert_called_once_with(
            user_id=user.pk,
            client_ip='127.0.0.1',
            device_type=None,
        )

    def test_update_me(self):
        query = '''
            mutation Mutation($input: UserMeInputType!) {
              updateMe(data: $input) {
                ok
                errors
              }
            }
        '''
        user = UserFactory.create()
        project = ProjectFactory.create()
        gallery_file = FileFactory.create()

        # With invalid attributes
        minput = dict(
            emailOptOuts=["news_and_updates", "join_requests", "haha-hunu"],  # Invalid options
            displayPicture=gallery_file.pk,  # File without access
            lastActiveProject=project.pk,  # Non-member Project
            language="en-us",
            firstName="Admin",
            lastName="Deep",
            organization="DFS",
        )
        # Without authentication -----
        content = self.query_check(query, minput=minput, assert_for_error=True)
        # With authentication -----
        self.force_login(user)
        content = self.query_check(query, minput=minput, okay=False)
        self.assertEqual(len(content['data']['updateMe']['errors']), 3, content)
        # With valid -----
        minput['emailOptOuts'] = ["news_and_updates", "join_requests"]  # Remove invalid option
        # Add ownership to file
        gallery_file.created_by = user
        gallery_file.save()
        # Add user to project
        project.add_member(user)
        content = self.query_check(query, minput=minput, okay=True)

    def test_me_last_active_project(self):
        query = '''
            query Query {
              me {
                lastActiveProject {
                    id
                    title
                }
              }
            }
        '''

        user = UserFactory.create()
        project1 = ProjectFactory.create()
        project2 = ProjectFactory.create()
        project3 = ProjectFactory.create()

        # --- Login
        self.force_login(user)
        # --- Without any project membership
        content = self.query_check(query)
        self.assertEqual(content['data']['me']['lastActiveProject'], None, content)
        # --- With a project membership + But no lastActiveProject set in profile
        project1.add_member(user)
        content = self.query_check(query)
        self.assertIdEqual(content['data']['me']['lastActiveProject']['id'], project1.pk, content)
        # --- With a project membership + lastActiveProject is set in profile
        project2.add_member(user)
        user.last_active_project = project2
        content = self.query_check(query)
        self.assertIdEqual(content['data']['me']['lastActiveProject']['id'], project2.pk, content)
        # --- With a project membership + (non-member) lastActiveProject is set in profile
        user.last_active_project = project3
        content = self.query_check(query)
        self.assertIdEqual(content['data']['me']['lastActiveProject']['id'], project2.pk, content)

    def test_me_allowed_features(self):
        query = '''
            query MyQuery {
              me {
                accessibleFeatures {
                  title
                  key
                  featureType
                }
              }
            }
        '''

        feature1 = FeatureFactory.create(key=Feature.FeatureKey.ANALYSIS)
        feature2 = FeatureFactory.create(key=Feature.FeatureKey.POLYGON_SUPPORT_GEO)
        FeatureFactory.create()
        user = UserFactory.create()

        # --- Login
        self.force_login(user)
        # --- Without any features
        content = self.query_check(query)
        self.assertEqual(len(content['data']['me']['accessibleFeatures']), 0, content)
        # --- With a project membership + But no lastActiveProject set in profile
        feature1.users.add(user)
        feature2.users.add(user)
        content = self.query_check(query)
        self.assertEqual(len(content['data']['me']['accessibleFeatures']), 2, content)
        self.assertEqual(content['data']['me']['accessibleFeatures'][0]['key'], self.genum(feature1.key), content)
        self.assertEqual(content['data']['me']['accessibleFeatures'][1]['key'], self.genum(feature2.key), content)

    def test_me_only_fields(self):
        query = '''
            query UserQuery($id: ID!) {
              me {
                id
                displayName
                jwtToken {
                  accessToken
                  expiresIn
                }
                organization
                lastName
                lastLogin
                language
                isActive
                firstName
                emailOptOuts
                email
                displayPictureUrl
                displayPicture
                lastActiveProject {
                    id
                    title
                }
              }
              user(id: $id) {
                organization
                lastName
                language
                isActive
                id
                firstName
                displayPictureUrl
                displayName
              }
              users {
                results {
                    organization
                    lastName
                    language
                    isActive
                    id
                    firstName
                    displayPictureUrl
                    displayName
                }
                page
                pageSize
              }
            }
        '''

        User.objects.all().delete()  # Clear all users if exists
        project = ProjectFactory.create()
        display_picture = FileFactory.create()
        # Create some users
        user = UserFactory.create(  # Will use this as requesting user
            organization='Deep',
            language='en-us',
            email_opt_outs=['join_requests'],
            last_login=timezone.now(),
            last_active_project=project,
            display_picture=display_picture,
        )
        project.add_member(user)
        # Other users
        for i in range(0, 3):
            other_last_user = UserFactory.create(
                organization=f'Deep {i}',
                language='en-us',
                email_opt_outs=['join_requests'],
                last_login=timezone.now(),
                last_active_project=project,
                display_picture=display_picture,
            )

        # This fields are only meant for `Me`
        only_me_fields = [
            'displayPicture', 'lastActiveProject', 'language', 'emailOptOuts',
            'email', 'lastLogin', 'jwtToken',
        ]
        # Without authentication -----
        content = self.query_check(query, assert_for_error=True, variables={'id': str(other_last_user.pk)})

        # With authentication -----
        self.force_login(user)
        content = self.query_check(query, variables={'id': str(other_last_user.pk)})
        self.assertEqual(len(content['data']['users']['results']), 4, content)  # 1 me + 3 others
        for field in only_me_fields:
            self.assertNotEqual(
                content['data']['me'].get(field), None, (field, content['data']['me'][field])
            )  # Shouldn't be None
            self.assertEqual(
                content['data']['user'].get(field), None, (field, content['data']['user'].get(field))
            )  # Should be None
        # check for display_picture_url
        self.assertNotEqual(content['data']['me']['displayPictureUrl'], None, content)
