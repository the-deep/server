import autofixture
from rest_framework import (
    test,
    status,
)
from jwt_auth.token import AccessToken, RefreshToken

from user.models import User
from project.models import ProjectRole
from project.permissions import get_project_permissions_value


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
        # This should be called here to access roles later
        self.create_project_roles()

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

    def assert_204(self, response):
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

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
            follow_fk=False,
            follow_m2m=False
        ).create_one()

        role = kwargs.get('role')

        if role and hasattr(obj, 'add_member'):
            obj.add_member(self.user, role=role)

        return obj

    def create_project_roles(self):
        # Remove roles if already exist. Right now, we just have global roles
        ProjectRole.objects.all().delete()
        # Creator role
        self.admin_role = ProjectRole.objects.create(
            title='Admin',
            lead_permissions=get_project_permissions_value('lead', '__all__'),
            entry_permissions=get_project_permissions_value(
                'entry', '__all__'),
            setup_permissions=get_project_permissions_value(
                'setup', '__all__'),
            export_permissions=get_project_permissions_value(
                'export', '__all__'),
            assessment_permissions=get_project_permissions_value(
                'assessment', '__all__'),
            is_creator_role=True
        )
        # Default role
        self.normal_role = ProjectRole.objects.create(
            title='Analyst',
            lead_permissions=get_project_permissions_value(
                'lead', '__all__'),
            entry_permissions=get_project_permissions_value(
                'entry', '__all__'),
            setup_permissions=get_project_permissions_value('setup', []),
            export_permissions=get_project_permissions_value(
                'export', ['create']),
            assessment_permissions=get_project_permissions_value(
                'assessment', '__all__'),
            is_default_role=True
        )
        self.view_only_role = ProjectRole.objects.create(
            title='ViewOnly',
            lead_permissions=get_project_permissions_value(
                'lead', ['view']
            ),
            entry_permissions=get_project_permissions_value(
                'entry', ['view']
            ),
            setup_permissions=get_project_permissions_value(
                'setup', []
            ),
            export_permissions=get_project_permissions_value(
                'export', []
            ),
            assessment_permissions=get_project_permissions_value(
                'assessment', ['view']
            ),
        )
