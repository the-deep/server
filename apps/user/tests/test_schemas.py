from unittest import mock
from django.conf import settings

from utils.graphene.tests import GraphqlTestCase

from user.models import User
from user.factories import UserFactory
from user.utils import (
    send_password_changed_notification,
    send_password_reset,
    send_account_activation,
)


class TestUserSchema(GraphqlTestCase):
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
        mutation_input = dict(email='xyz@xyz.com', password='pasword-xyz')
        response = self.query(self.login_mutation, input_data=mutation_input)
        self.assertResponseNoErrors(response)
        content = response.json()
        self.assertFalse(content['data']['login']['ok'], content)

        # Try with real user
        user = UserFactory.create(email=mutation_input['email'])
        response = self.query(self.login_mutation, input_data=dict(email=user.email, password=user.password_text))
        self.assertResponseNoErrors(response)
        content = response.json()
        self.assertTrue(content['data']['login']['ok'], content)
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
            response = self.query(
                self.login_mutation,
                input_data=dict(
                    email=user.email,
                    password='wrong-password',
                    captcha='captcha',
                ),
            )
            self.assertResponseNoErrors(response)
            content = response.json()
            user.refresh_from_db()
            self.assertFalse(content['data']['login']['ok'], content)

        def _valid_login():
            response = self.query(
                self.login_mutation,
                input_data=dict(
                    email=user.email,
                    password=user.password_text,
                    captcha='captcha',
                ),
            )
            self.assertResponseNoErrors(response)
            content = response.json()
            return content

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
        content = _valid_login()
        self.assertFalse(content['data']['login']['ok'], content)

        # mock activation link logic
        user.profile.login_attempts = 0
        user.profile.save(update_fields=['login_attempts'])

        content = _valid_login()
        self.assertTrue(content['data']['login']['ok'], content)

    @mock.patch('jwt_auth.captcha.requests')
    @mock.patch('user.serializers.send_password_reset', side_effect=send_password_reset)
    def test_register(self, send_password_reset_mock, captch_requests_mock):
        register_mutation = '''
            mutation Mutation($input: RegisterInputType!) {
              register(data: $input) {
                ok
                captchaRequired
                errors
              }
            }
        '''
        # input without email
        mutation_input = dict(
            email='invalid-email',
            firstName='john',
            lastName='cena',
            organization='the-deep',
            captcha='captcha',
        )

        def _call_register():
            response = self.query(register_mutation, input_data=mutation_input)
            self.assertResponseNoErrors(response)
            return response.json()

        # With invalid captcha
        captch_requests_mock.post.return_value.json.return_value = {'success': False}
        content = _call_register()
        self.assertFalse(content['data']['register']['ok'], content)

        # With valid captcha now
        captch_requests_mock.post.return_value.json.return_value = {'success': True}
        # With invalid email
        content = _call_register()
        self.assertFalse(content['data']['register']['ok'], content)
        self.assertTrue(len(content['data']['register']['errors']) == 1, content)

        # With valid input
        mutation_input['email'] = 'john@cena.com'
        with self.captureOnCommitCallbacks(execute=True):
            content = _call_register()
        self.assertTrue(content['data']['register']['ok'], content)
        # Make sure password reset message is send
        user = User.objects.get(email=mutation_input['email'])
        send_password_reset_mock.assert_called_once_with(user=user, welcome=True)

    def test_logout(self):
        me_query = '''
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

        # # Login
        self.force_login()
        # Query Me (Success)
        response = self.query(me_query)
        content = response.json()
        self.assertEqual(content['data']['me']['id'], str(self.user.id), content)
        self.assertEqual(content['data']['me']['email'], self.user.email, content)

        # # Logout
        response = self.query(logout_mutation)
        self.assertResponseNoErrors(response)
        content = response.json()
        self.assertTrue(content['data']['logout']['ok'], content)

        # Query Me (with error)
        response = self.query(me_query)
        content = response.json()
        self.assertIsNotNone(content['errors'], content)

    @mock.patch('jwt_auth.captcha.requests')
    @mock.patch('user.serializers.send_password_reset', side_effect=send_password_reset)
    def test_password_reset(self, send_password_reset_mock, captch_requests_mock):
        password_rest_mutation = '''
            mutation Mutation($input: ResetPasswordInputType!) {
              resetPassword(data: $input) {
                ok
                captchaRequired
                errors
              }
            }
        '''
        # input without email
        mutation_input = dict(
            email='invalid-email',
            captcha='captcha',
        )

        def _call_password_reset():
            response = self.query(password_rest_mutation, input_data=mutation_input)
            self.assertResponseNoErrors(response)
            return response.json()

        # With invalid captcha
        captch_requests_mock.post.return_value.json.return_value = {'success': False}
        content = _call_password_reset()
        self.assertFalse(content['data']['resetPassword']['ok'], content)

        # With valid captcha now
        captch_requests_mock.post.return_value.json.return_value = {'success': True}
        # With invalid email
        content = _call_password_reset()
        self.assertFalse(content['data']['resetPassword']['ok'], content)
        self.assertTrue(len(content['data']['resetPassword']['errors']) == 1, content)

        # With unknown user email
        mutation_input['email'] = 'john@cena.com'
        content = _call_password_reset()
        self.assertFalse(content['data']['resetPassword']['ok'], content)
        self.assertTrue(len(content['data']['resetPassword']['errors']) == 1, content)

        # With known user email
        UserFactory.create(email=mutation_input['email'])
        content = _call_password_reset()
        self.assertTrue(content['data']['resetPassword']['ok'], content)
        # Make sure password reset message is send
        user = User.objects.get(email=mutation_input['email'])
        send_password_reset_mock.assert_called_once_with(user=user)

    @mock.patch(
        'user.serializers.send_password_changed_notification.delay',
        side_effect=send_password_changed_notification.delay,
    )
    def test_password_change(self, send_password_changed_notification_mock):
        password_rest_mutation = '''
            mutation Mutation($input: PasswordChangeInputType!) {
              changePassword(data: $input) {
                ok
                errors
              }
            }
        '''
        # input without email
        mutation_input = dict(oldPassword='', newPassword='new-password-123')

        def _call_password_change(assert_for_error=False):
            response = self.query(password_rest_mutation, input_data=mutation_input)
            if assert_for_error:
                self.assertResponseErrors(response)
            else:
                self.assertResponseNoErrors(response)
            return response.json()

        # Without authentication
        content = _call_password_change(assert_for_error=True)

        # Without authentication
        user = UserFactory.create()
        self.force_login(user)

        # With invalid old password
        content = _call_password_change()
        self.assertFalse(content['data']['changePassword']['ok'], content)
        self.assertTrue(len(content['data']['changePassword']['errors']) == 1, content)

        # With valid password
        mutation_input['oldPassword'] = user.password_text
        with self.captureOnCommitCallbacks(execute=True):
            content = _call_password_change()
        self.assertTrue(content['data']['changePassword']['ok'], content)
        # Make sure password reset message is send
        send_password_changed_notification_mock.assert_called_once()
        send_password_changed_notification_mock.assert_called_once_with(
            user_id=user.pk,
            client_ip='127.0.0.1',
            device_type=None,
        )
