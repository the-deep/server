import os
import json
import pytz
import shutil
import datetime
from enum import Enum
from unittest.mock import patch
from typing import Union

from factory import random as factory_random
from snapshottest.django import TestCase as SnapShotTextCase
from django.utils import timezone
from django.core import management
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.db import models
# dramatiq test case: setupclass is not properly called
# from django_dramatiq.test import DramatiqTestCase
from graphene_django.utils import GraphQLTestCase as BaseGraphQLTestCase
from rest_framework import status

from deep.middleware import _set_current_request
from deep.tests.test_case import (
    TEST_CACHES,
    TEST_AUTH_PASSWORD_VALIDATORS,
    TEST_EMAIL_BACKEND,
    TEST_FILE_STORAGE,
)

from analysis_framework.models import AnalysisFramework, AnalysisFrameworkRole
from project.permissions import get_project_permissions_value
from project.models import ProjectRole

User = get_user_model()
TEST_MEDIA_ROOT = 'media-temp'


class CommonSetupClassMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # add necessary stuffs

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # clear the temporary media files
        try:
            shutil.rmtree(os.path.join(settings.BASE_DIR, TEST_MEDIA_ROOT), ignore_errors=True)
        except FileNotFoundError:
            pass


@override_settings(
    EMAIL_BACKEND=TEST_EMAIL_BACKEND,
    MEDIA_ROOT=TEST_MEDIA_ROOT,
    DEFAULT_FILE_STORAGE=TEST_FILE_STORAGE,
    CACHES=TEST_CACHES,
    AUTH_PASSWORD_VALIDATORS=TEST_AUTH_PASSWORD_VALIDATORS,
    CELERY_TASK_ALWAYS_EAGER=True,
)
class GraphQLTestCase(CommonSetupClassMixin, BaseGraphQLTestCase):
    """
    GraphQLTestCase with custom helper methods
    """

    GRAPHQL_SCHEMA = 'deep.schema.schema'
    ENABLE_NOW_PATCHER = False
    PATCHER_NOW_VALUE = datetime.datetime(2021, 1, 1, 0, 0, 0, 123456, tzinfo=pytz.UTC)

    def _setup_premailer_patcher(self, mock):
        mock.get.return_value.text = ''
        mock.post.return_value.text = ''

    def setUp(self):
        super().setUp()
        self.create_project_roles()
        self.create_af_roles()
        self.premailer_patcher_requests = patch('premailer.premailer.requests')
        self._setup_premailer_patcher(self.premailer_patcher_requests.start())
        if self.ENABLE_NOW_PATCHER:
            self.now_patcher = patch('django.utils.timezone.now')
            self.now_datetime = self.PATCHER_NOW_VALUE
            self.now_datetime_str = lambda: self.now_datetime.isoformat()
            self.now_patcher.start().side_effect = lambda: self.now_datetime

    def tearDown(self):
        _set_current_request()  # Clear request
        if hasattr(self, 'now_patcher'):
            self.now_patcher.stop()
        self.premailer_patcher_requests.stop()
        super().tearDown()

    def force_login(self, user, refresh_from_db=False):
        if refresh_from_db:
            user.refresh_from_db()
        self.client.force_login(user)

    def logout(self):
        self.client.logout()

    def genum(self, _enum: Union[models.TextChoices, models.IntegerChoices, Enum]):
        """
        Return appropriate enum value.
        """
        return _enum.name

    def assertResponseErrors(self, resp, msg=None):
        """
        Assert that the call went through correctly but with error. 200 means the syntax is ok,
        if there are `errors`, the call wasn't fine.
        :resp HttpResponse: Response
        """
        content = json.loads(resp.content)
        self.assertEqual(resp.status_code, 200, msg or content)
        self.assertIn("errors", list(content.keys()), msg or content)

    def query_check(self, query, minput=None, mnested=None, assert_for_error=False, okay=None, **kwargs) -> dict:
        if minput:
            response = self.query(query, input_data=minput, **kwargs)
        else:
            response = self.query(query, **kwargs)
        content = response.json()
        if assert_for_error:
            self.assertResponseErrors(response)
        else:
            self.assertResponseNoErrors(response)
            if okay is not None:
                _content = content['data']
                if mnested:
                    for key in mnested:
                        _content = _content[key]
                for key, datum in _content.items():
                    if key == '__typename':
                        continue
                    okay_response = datum.get('ok')
                    if okay:
                        self.assertTrue(okay_response, content)
                    else:
                        self.assertFalse(okay_response, content)
        return content

    def create_project_roles(self):
        # Remove roles if already exist. Right now, we just have global roles
        ProjectRole.objects.all().delete()

        def _create_role(title, _type, level=1, is_default_role=False):
            # NOTE: Graphql endpoints will use static permission (Will remove dynamic permission in future)
            # TODO: Migrate current dynamic permission to static ones.
            return ProjectRole.objects.create(
                title=title,
                lead_permissions=get_project_permissions_value('lead', '__all__'),
                entry_permissions=get_project_permissions_value('entry', '__all__'),
                setup_permissions=get_project_permissions_value('setup', '__all__'),
                export_permissions=get_project_permissions_value('export', '__all__'),
                assessment_permissions=get_project_permissions_value('assessment', '__all__'),
                is_creator_role=False,
                level=level,
                is_default_role=is_default_role,
                type=_type,
            )

        # TODO: Make sure merge roles have all the permissions
        # Follow deep.permissions.py PERMISSION_MAP for permitted actions.
        self.project_role_reader_non_confidential = _create_role(
            'Reader (Non Confidential)',
            ProjectRole.Type.READER_NON_CONFIDENTIAL,
            level=800,
        )
        self.project_role_reader = _create_role(
            'Reader',
            ProjectRole.Type.READER,
            level=400,
        )
        self.project_role_member = _create_role(
            'Member',
            ProjectRole.Type.MEMBER,
            level=200,
            is_default_role=True,
        )
        self.project_role_admin = _create_role(
            'Admin',
            ProjectRole.Type.ADMIN,
            level=100,
        )
        self.project_role_owner = _create_role(
            'Project Owner',
            ProjectRole.Type.PROJECT_OWNER,
            level=1,
        )
        self.project_base_access = _create_role(
            'Base Access',
            ProjectRole.Type.UNKNOWN,
            level=999999,
        )

    def create_af_roles(self):  # Create Analysis Framework Roles
        # Remove roles if already exist. Right now, we just have global roles
        AnalysisFrameworkRole.objects.all().delete()

        def _create_role(title, _type, permissions=dict, is_private_role=False, is_default_role=False):
            # NOTE: Graphql endpoints will use static permission (Will remove dynamic permission in future)
            # TODO: Migrate current dynamic permission to static ones.
            return AnalysisFrameworkRole.objects.create(
                title=title,
                **permissions,
                is_private_role=is_private_role,
                is_default_role=is_default_role,
                type=_type,
            )

        # Follow deep.permissions.py PERMISSION_MAP for permitted actions.
        public_temp_af = AnalysisFramework()
        private_temp_af = AnalysisFramework(is_private=True)

        self.af_editor = _create_role(
            'Editor',
            AnalysisFrameworkRole.Type.EDITOR,
            permissions=public_temp_af.get_editor_permissions()
        )
        self.af_owner = _create_role(
            'Owner',
            AnalysisFrameworkRole.Type.OWNER,
            permissions=public_temp_af.get_owner_permissions(),
        )
        self.af_default = _create_role(
            'Default',
            AnalysisFrameworkRole.Type.DEFAULT,
            permissions=public_temp_af.get_default_permissions(),
            is_default_role=True,
        )
        self.af_private_editor = _create_role(
            'Private Editor',
            AnalysisFrameworkRole.Type.PRIVATE_EDITOR,
            permissions=private_temp_af.get_editor_permissions(),
            is_private_role=True,
        )
        self.af_private_owner = _create_role(
            'Private Owner',
            AnalysisFrameworkRole.Type.PRIVATE_OWNER,
            permissions=private_temp_af.get_owner_permissions(),
            is_private_role=True,
        )
        self.af_private_viewer = _create_role(
            'Private Viewer',
            AnalysisFrameworkRole.Type.PRIVATE_VIEWER,
            permissions=private_temp_af.get_default_permissions(),
            is_private_role=True,
            is_default_role=True,
        )

    def assertListIds(
        self,
        current_list, excepted_list, message=None,
        get_current_list_id=lambda x: str(x['id']),
        get_excepted_list_id=lambda x: str(x.id),
    ):
        self.assertEqual(
            set([get_current_list_id(item) for item in current_list]),
            set([get_excepted_list_id(item) for item in excepted_list]),
            message,
        )

    def assertNotListIds(
        self,
        current_list, excepted_list, message=None,
        get_current_list_id=lambda x: str(x['id']),
        get_not_excepted_list_id=lambda x: str(x.id),
    ):
        self.assertNotEqual(
            set([get_current_list_id(item) for item in current_list]),
            set([get_not_excepted_list_id(item) for item in excepted_list]),
            message,
        )

    def assertIdEqual(self, excepted, real, message=None):
        return self.assertEqual(str(excepted), str(real), message)

    def assertCustomDictEqual(self, excepted, real, message=None, ignore_keys=[], only_keys=[]):
        def _filter_by_keys(_dict, keys, exclude=False):
            def _include(key):
                if exclude:
                    return key not in keys
                return key in keys
            return {
                key: value
                for key, value in _dict.items()
                if _include(key)
            }

        if only_keys:
            assert _filter_by_keys(excepted, keys=only_keys) == _filter_by_keys(real, keys=only_keys), message
        elif ignore_keys:
            assert _filter_by_keys(excepted, keys=ignore_keys, exclude=True) \
                == _filter_by_keys(real, keys=ignore_keys, exclude=True),\
                message
        else:
            assert excepted == real, message

    def assertQuerySetIdEqual(self, l1, l2):
        return self.assertEqual(
            sorted([each.id for each in l1]),
            sorted([each.id for each in l2]),
        )

    def get_media_url(self, file):
        return f'http://testserver/media/{file}'

    def update_obj(self, obj, **fields):
        for key, value in fields.items():
            setattr(obj, key, value)
        obj.save()
        return obj

    def get_datetime_str(self, _datetime):
        return _datetime.isoformat()

    def get_date_str(self, _datetime):
        return _datetime.strftime('%Y-%m-%d')

    def get_aware_datetime(self, *args, **kwargs):
        return timezone.make_aware(datetime.datetime(*args, **kwargs))

    def get_aware_datetime_str(self, *args, **kwargs):
        return self.get_datetime_str(self.get_aware_datetime(*args, **kwargs))

    # Some Rest helper functions
    def assert_http_code(self, response, status_code):
        error_resp = getattr(response, 'data', None)
        mesg = error_resp
        if type(error_resp) is dict and 'errors' in error_resp:
            mesg = error_resp['errors']
        return self.assertEqual(response.status_code, status_code, mesg)

    def assert_400(self, response):
        self.assert_http_code(response, status.HTTP_400_BAD_REQUEST)

    def assert_403(self, response):
        self.assert_http_code(response, status.HTTP_403_FORBIDDEN)

    def assert_200(self, response):
        self.assert_http_code(response, status.HTTP_200_OK)

    def assertExtraNumQueries(self, count):
        """
        Append prefix + postfix queries counts
        Captured queries were:
        1. SAVEPOINT QUERY
        2. django-session QUERY
        3. Request User QUERY
        N. View based QUERY
        Final. RELEASE SAVEPOINT QUERY
        """
        return self.assertNumQueries(4 + count)


class GraphQLSnapShotTestCase(GraphQLTestCase, SnapShotTextCase):
    """
    This TestCase can be used with `self.assertMatchSnapshot`.
    Make sure to only include snapshottests as we are using database flush.
    """
    maxDiff = None
    factories_used = []

    def setUp(self):
        self.ENABLE_NOW_PATCHER = True  # We need to set this or snapshot will have different dates
        # XXX: This is hacky way to make sure id aren't changed in snapshot. This makes the test slower.
        management.call_command("flush", "--no-input")
        factory_random.reseed_random(42)
        for factory in self.factories_used:
            factory.reset_sequence()
        super().setUp()

    def tearDown(self):
        super().tearDown()


@override_settings(
    EMAIL_BACKEND=TEST_EMAIL_BACKEND,
    DEFAULT_FILE_STORAGE=TEST_FILE_STORAGE,
    MEDIA_ROOT=TEST_MEDIA_ROOT,
    CACHES=TEST_CACHES,
    AUTH_PASSWORD_VALIDATORS=TEST_AUTH_PASSWORD_VALIDATORS,
)
class CommonTestCase(CommonSetupClassMixin, TestCase):
    pass
