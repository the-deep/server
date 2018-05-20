import autofixture
from rest_framework import (
    test,
    status,
)
from jwt_auth.token import AccessToken, RefreshToken
from user.models import User


class TestCase(test.APITestCase):
    def setUp(self):
        self.root_user = User.objects.create_user(
            username='root@test.com',
            first_name='Root',
            last_name='Toot',
            password='admin123',
            email='root@test.com',
            is_superuser=True,
            is_staff=True,
        )

        self.user = User.objects.create_user(
            username='jon@dave.com',
            first_name='Jon',
            last_name='Mon',
            password='test123',
            email='jon@dave.com',
        )

    def authenticate(self, user=None):
        user = user or self.user
        access = AccessToken.for_user(user)
        refresh = RefreshToken.for_access_token(access)

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer {}'.format(access.encode())
        )

        return access.encode(), refresh.encode()

    def authenticate_root(self):
        self.authenticate(self.root_user)

    def assert_200(self, response):
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def assert_201(self, response):
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def assert_400(self, response):
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def assert_403(self, response):
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def create(self, model, **kwargs):
        if not kwargs.get('created_by'):
            kwargs['created_by'] = self.user
        if not kwargs.get('modified_by'):
            kwargs['modified_by'] = self.user

        obj = autofixture.base.AutoFixture(
            model, field_values=kwargs,
            generate_fk=True,
        ).create_one()

        if hasattr(obj, 'add_member'):
            obj.add_member(self.user, role='admin')

        return obj
