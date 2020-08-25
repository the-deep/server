import os
import types
import inspect
from mock import patch

import autofixture
from rest_framework import (
    test,
    status,
)
from jwt_auth.token import AccessToken, RefreshToken

from django.db import DEFAULT_DB_ALIAS, connections
from django.conf import settings
from user.models import User
from project.models import ProjectRole, Project
from project.permissions import get_project_permissions_value
from lead.models import Lead
from entry.models import Entry
from gallery.models import File
from analysis_framework.models import AnalysisFramework
from ary.models import AssessmentTemplate, Assessment


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

    def tearDown(self):
        for file_path in self.deep_test_files_path:
            if os.path.isfile(file_path):
                os.unlink(file_path)

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

    def assertEqualWithWarning(self, expected, real):
        try:
            self.assertEqual(expected, real)
        except AssertionError:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning('', exc_info=True)

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
        # ARY full-access role
        self.ary_create_role = ProjectRole.objects.create(
            title='AryViewOnly',
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
                'assessment', '__all__'
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

    @classmethod
    def captureOnCommitCallbacks(cls, *, using=DEFAULT_DB_ALIAS, execute=False):
        return _CaptureOnCommitCallbacksContext(using=using, execute=execute)


class _CaptureOnCommitCallbacksContext:
    def __init__(self, *, using=DEFAULT_DB_ALIAS, execute=False):
        self.using = using
        self.execute = execute
        self.callbacks = None

    def __enter__(self):
        if self.callbacks is not None:
            raise RuntimeError("Cannot re-enter captureOnCommitCallbacks()")
        self.start_count = len(connections[self.using].run_on_commit)
        self.callbacks = []
        return self.callbacks

    def __exit__(self, exc_type, exc_valuei, exc_traceback):
        run_on_commit = connections[self.using].run_on_commit[self.start_count:]
        self.callbacks[:] = [func for sids, func in run_on_commit]
        if exc_type is None and self.execute:
            for callback in self.callbacks:
                callback()


def mock_module_function_with_return_value(module_function_full_name, return_value):
    """
    Example: Whenever we need to mock a function from a module, say lead.serializers.get_duplicate_leads,
    we decorate the method with @patch('lead.serializers.get_duplicate_leads') this will return a function with
    an extra paramter, the mock object, say mock_obj. We can then set the return value or raise exception and do
    many things with the mock object.

    This function takes a function path string and it's return value and mocks a given function
    """
    def decorator(method):
        patch_decorator = patch(module_function_full_name)
        # When we apply this decorator, the new function will have an extra argument which is the
        # mock object

        def new_func(self, *args, **kwargs):
            print(args, kwargs)
            # Since this function is going to be decorated, we are sure that this will have
            # an added argument, which is the mock object. So we can safely access args[-1]
            args[-1].return_value = return_value
            method(self, *args[:-1], **kwargs)  # but our method does not take extra arg so omit the last arg(i.e. the mock object)

        return patch_decorator(new_func)  # this is where the magic of adding a new arg happens
    return decorator


# This is not used.
def decorate_class_with(method_decorator):
    """
    This is used to decorate a class' all methods with the given method decorator
    """
    def decorator(cls):
        for name, fn in inspect.getmembers(cls):
            if isinstance(fn, types.FunctionType):
                setattr(cls, name, method_decorator(fn))
        return cls
    return decorator
