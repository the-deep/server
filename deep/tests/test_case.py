import os
import autofixture
from rest_framework import (
    test,
    status,
)

import datetime
from django.test import override_settings
from django.utils import timezone
from django.conf import settings

from deep.middleware import _set_current_request as _set_middleware_current_request
from user.models import User
from project.models import ProjectRole, Project
from project.permissions import get_project_permissions_value
from lead.models import Lead
from entry.models import Entry
from gallery.models import File
from analysis_framework.models import AnalysisFramework
from ary.models import AssessmentTemplate, Assessment


TEST_MEDIA_ROOT = 'rest-media-temp'
TEST_EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
TEST_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake-rest',
    }
}
DUMMY_TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'LOCATION': 'unique-snowflake-rest',
    }
}
TEST_AUTH_PASSWORD_VALIDATORS = []


@override_settings(
    DEBUG=True,
    EMAIL_BACKEND=TEST_EMAIL_BACKEND,
    MEDIA_ROOT=TEST_MEDIA_ROOT,
    DEFAULT_FILE_STORAGE=TEST_FILE_STORAGE,
    CACHES=TEST_CACHES,
    CELERY_TASK_ALWAYS_EAGER=True,
)
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
        self.deep_test_files_path = []
        if not os.path.exists(TEST_MEDIA_ROOT):
            os.makedirs(TEST_MEDIA_ROOT)
        super().setUp()

    def tearDown(self):
        super().tearDown()
        _set_middleware_current_request(None)
        for file_path in self.deep_test_files_path:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        # Unlink any files created while running test
        for file in File.objects.all():
            if file.file:
                file_path = file.file.path
                if os.path.isfile(file_path):
                    os.unlink(file_path)

    def authenticate(self, user=None):
        user = user or self.user
        self.client.force_login(user)

    def authenticate_root(self):
        self.authenticate(self.root_user)

    def assertEqualWithWarning(self, expected, real):
        try:
            self.assertEqual(expected, real)
        except AssertionError:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning('', exc_info=True)

    def assert_http_code(self, response, status_code, msg=None):
        error_resp = getattr(response, 'data', None)
        mesg = msg or error_resp
        if type(error_resp) is dict and 'errors' in error_resp:
            mesg = error_resp['errors']
        return self.assertEqual(response.status_code, status_code, mesg)

    def assert_200(self, response):
        self.assert_http_code(response, status.HTTP_200_OK)

    def assert_201(self, response):
        self.assert_http_code(response, status.HTTP_201_CREATED)

    def assert_202(self, response):
        self.assert_http_code(response, status.HTTP_202_ACCEPTED)

    def assert_204(self, response):
        self.assert_http_code(response, status.HTTP_204_NO_CONTENT)

    def assert_302(self, response):
        self.assert_http_code(response, status.HTTP_302_FOUND)

    def assert_400(self, response):
        self.assert_http_code(response, status.HTTP_400_BAD_REQUEST)

    def assert_401(self, response):
        self.assert_http_code(response, status.HTTP_401_UNAUTHORIZED)

    def assert_403(self, response):
        self.assert_http_code(response, status.HTTP_403_FORBIDDEN)

    def assert_404(self, response):
        self.assert_http_code(response, status.HTTP_404_NOT_FOUND)

    def assert_405(self, response):
        self.assert_http_code(response, status.HTTP_405_METHOD_NOT_ALLOWED)

    def assert_500(self, response):
        self.assert_http_code(response, status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            type=ProjectRole.Type.PROJECT_OWNER,
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
            type=ProjectRole.Type.ADMIN,
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
            type=ProjectRole.Type.MEMBER,
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
            title='Viewer',
            type=ProjectRole.Type.READER,
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

    def create_user(self, **fields):
        return self.create(User, **fields)

    def create_project(self, **fields):
        data = {
            **fields,
            'analysis_framework': fields.pop('analysis_framework', None) or self.create(AnalysisFramework),
            'role': fields.pop('role', self.admin_role),
        }
        if fields.pop('create_assessment_template', False):
            data['assessment_template'] = self.create(AssessmentTemplate)
        return self.create(Project, **data)

    def create_gallery_file(self):
        url = '/api/v1/files/'

        path = os.path.join(settings.TEST_DIR, 'documents')
        self.supported_file = os.path.join(path, 'doc.docx')
        data = {
            'title': 'Test file',
            'file': open(self.supported_file, 'rb'),
            'isPublic': True,
        }

        self.authenticate()
        self.client.post(url, data, format='multipart')

        file = File.objects.last()
        self.deep_test_files_path.append(file.file.path)
        return file

    def create_lead(self, **fields):
        project = fields.pop('project', None) or self.create_project()
        return self.create(Lead, project=project, **fields)

    def create_entry(self, **fields):
        project = fields.pop('project', None) or self.create_project()
        lead = fields.pop('lead', None) or self.create_lead(project=project)
        return self.create(
            Entry, lead=lead, project=lead.project,
            analysis_framework=lead.project.analysis_framework,
            **fields
        )

    def create_assessment(self, **fields):
        lead = fields.pop('lead', None) or self.create_lead()
        return self.create(
            Assessment,
            lead=lead,
            project=lead.project,
            **fields
        )

    def update_obj(self, obj, **fields):
        for key, value in fields.items():
            setattr(obj, key, value)
        obj.save()
        return obj

    def post_filter_test(self, url, filters, count=1, skip_auth=False):
        params = {
            'filters': [[k, v] for k, v in filters.items()]
        }

        if skip_auth:
            self.authenticate()
        response = self.client.post(url, params)
        self.assert_200(response)

        r_data = response.json()
        self.assertEqual(len(r_data['results']), count, f'Filters: {filters}')
        return response

    def get_datetime_str(self, _datetime):
        return _datetime.strftime('%Y-%m-%d%z')

    def get_date_str(self, _datetime):
        return _datetime.strftime('%Y-%m-%d')

    def get_aware_datetime(self, *args, **kwargs):
        return timezone.make_aware(datetime.datetime(*args, **kwargs))

    def get_aware_datetime_str(self, *args, **kwargs):
        return self.get_datetime_str(self.get_aware_datetime(*args, **kwargs))
