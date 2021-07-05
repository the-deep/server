from unittest import mock
from django.conf import settings

from utils.graphene.tests import GraphqlTestCase

from user.factories import UserFactory


class TestUserSchema(GraphqlTestCase):
    def setUp(self):
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
        self.assertEqual(content['data']['login']['result']['id'], str(user.id))
        self.assertEqual(content['data']['login']['result']['email'], user.email)

    @mock.patch('jwt_auth.captcha.requests')
    @mock.patch('user.serializers.send_account_activation')
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
                    hcaptchaResponse='captcha',
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
                    hcaptchaResponse='captcha',
                ),
            )
            self.assertResponseNoErrors(response)
            content = response.json()
            return content

        captch_requests_mock.post.return_value.json.return_value = {'success': False}
        user = UserFactory.create()
        # For MAX_LOGIN_ATTEMPTS_FOR_CAPTCHA count failed login attempt
        for attempt in range(1, 5):
            _invalid_login()
            if attempt < settings.MAX_LOGIN_ATTEMPTS_FOR_CAPTCHA:
                self.assertEqual(user.profile.login_attempts, attempt)
            else:
                # Count stoped (when valid captch is not provided)
                self.assertEqual(user.profile.login_attempts, settings.MAX_LOGIN_ATTEMPTS_FOR_CAPTCHA)
        # After MAX_LOGIN_ATTEMPTS_FOR_CAPTCHA count failed captcha is required
        captch_requests_mock.post.return_value.json.return_value = {'success': True}
        for attempt in range(
            settings.MAX_LOGIN_ATTEMPTS_FOR_CAPTCHA + 1,
            settings.MAX_LOGIN_ATTEMPTS + 2,
        ):
            _invalid_login()
            if user.profile.login_attempts > settings.MAX_LOGIN_ATTEMPTS:
                # Email is sent
                send_account_activation_mock.assert_called_once_with(user)
                # Not accepting any new attempt
                self.assertEqual(user.profile.login_attempts, settings.MAX_LOGIN_ATTEMPTS + 1)
            else:
                send_account_activation_mock.assert_not_called()
                self.assertEqual(user.profile.login_attempts, attempt)
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
        self.assertEqual(content['data']['me']['id'], str(self.user.id))
        self.assertEqual(content['data']['me']['email'], self.user.email)

        # # Logout
        response = self.query(logout_mutation)
        self.assertResponseNoErrors(response)
        content = response.json()
        self.assertTrue(content['data']['logout']['ok'], content)

        # Query Me (with error)
        response = self.query(me_query)
        content = response.json()
        self.assertIsNotNone(content['errors'], content)
