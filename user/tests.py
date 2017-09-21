from user.models import User


class AuthMixin():
    """
    Auth mixin
    Creates users and generates auth token
    """
    def get_auth(self):
        """
        Generates HTTP_AUTHORIZATION
        """
        auth = 'Bearer {0}'.format(self.get_access_token())
        return auth

    def get_access_token(self):
        """
        Create user
        Generate auth token
        """
        self.user = User.objects.create_user(
            username='test@test.com',
            first_name='Test',
            last_name='Test',
            password='admin123',
            email='test@test.com',
        )
        result = self.client.post(
            '/api/v1/token/',
            data={
                'username': 'test@test.com',
                'password': 'admin123',
            }, format='json')
        return result.data['access']
