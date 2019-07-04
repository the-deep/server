import autofixture
from rest_framework import (
    test,
    status,
)
from jwt_auth.token import AccessToken, RefreshToken

from user.models import User
from project.models import ProjectRole, Project
from project.permissions import get_project_permissions_value
from lead.models import Lead
from entry.models import Entry
from analysis_framework.models import AnalysisFramework


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

    def assert_202(self, response):
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def assert_204(self, response):
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def assert_302(self, response):
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def assert_400(self, response):
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def assert_403(self, response):
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def assert_404(self, response):
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def assert_405(self, response):
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def assert_500(self, response):
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            title='Clairvoyant One',
            lead_permissions=get_project_permissions_value('lead', '__all__'),
            entry_permissions=get_project_permissions_value(
                'entry', '__all__'),
            setup_permissions=get_project_permissions_value(
                'setup', '__all__'),
            export_permissions=get_project_permissions_value(
                'export', '__all__'),
            assessment_permissions=get_project_permissions_value(
                'assessment', '__all__'),
            is_creator_role=True,
            level=1,
        )
        # Smaller admin role
        self.smaller_admin_role = ProjectRole.objects.create(
            title='Admin',
            lead_permissions=get_project_permissions_value('lead', '__all__'),
            entry_permissions=get_project_permissions_value(
                'entry', '__all__'),
            setup_permissions=get_project_permissions_value(
                'setup', ['modify']),
            export_permissions=get_project_permissions_value(
                'export', '__all__'),
            assessment_permissions=get_project_permissions_value(
                'assessment', '__all__'),
            is_creator_role=True,
            level=100,
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
            is_default_role=True,
            level=100,
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

    def post_and_check_201(self, url, data, model, fields):
        model_count = model.objects.count()

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(model.objects.count(), model_count + 1),\
            f'One more {model} should have been created'

        for field in fields:
            self.assertEqual(response.data[field], data[field])

        return response

    def create_project(self):
        analysis_framework = self.create(AnalysisFramework)
        return self.create(
            Project, analysis_framework=analysis_framework,
            role=self.admin_role
        )

    def create_lead(self):
        project = self.create_project()
        return self.create(Lead, project=project)

    def create_entry(self, **fields):
        lead = self.create_lead()
        return self.create(
            Entry, lead=lead, project=lead.project,
            analysis_framework=lead.project.analysis_framework,
            **fields
        )
