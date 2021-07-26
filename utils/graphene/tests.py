import os
import json
import pytz
import shutil
import datetime
from enum import Enum
from unittest.mock import patch

from snapshottest.django import TestCase as SnapShotTextCase
from django.core import management
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
# dramatiq test case: setupclass is not properly called
# from django_dramatiq.test import DramatiqTestCase
from graphene_django.utils import GraphQLTestCase as BaseGraphQLTestCase
from project.permissions import get_project_permissions_value
from project.models import ProjectRole

User = get_user_model()
TEST_MEDIA_ROOT = 'media-temp'
TEST_EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
TEST_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
TEST_AUTH_PASSWORD_VALIDATORS = []


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
            shutil.rmtree(os.path.join(settings.BASE_DIR, TEST_MEDIA_ROOT))
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

    def setUp(self):
        super().setUp()
        self.create_project_roles()

    def force_login(self, user):
        self.client.force_login(user)

    def genum(self, _enum: Enum):
        """
        Return appropriate enum value.
        """
        if isinstance(_enum.value, int):
            return f'A_{_enum.value}'
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

        def _create_role(title, is_default_role=False):
            # NOTE: Graphql endpoints will use static permission (Will remove dynamic permission in future)
            # TODO: Migrate current dynamic permission to static ones.
            return ProjectRole.objects.create(
                title=title,
                lead_permissions=get_project_permissions_value('lead', '__all__'),
                entry_permissions=get_project_permissions_value('entry', '__all__'),
                setup_permissions=get_project_permissions_value('setup', '__all__'),
                export_permissions=get_project_permissions_value('export', '__all__'),
                assessment_permissions=get_project_permissions_value('assessment', '__all__'),
                is_creator_role=True,
                level=1,
                is_default_role=is_default_role,
            )

        # TODO: Add test for each permission actions
        # Follow deep.permissions.py PERMISSION_MAP for permitted actions.
        self.role_viewer_non_confidential = _create_role('Viewer (Non Confidential)')
        self.role_viewer = _create_role('Viewer')
        self.role_reader = _create_role('Reader (Non Confidential)')
        self.role_reader = _create_role('Reader')
        self.role_sourcer = _create_role('Sourcer')
        self.role_analyst = _create_role('Analyst', is_default_role=True)
        self.role_admin = _create_role('Admin')
        self.role_clairvoyant_one = _create_role('Clairvoyant One')

    def assertListIds(
        self,
        current_list, excepted_list, message,
        get_current_list_id=lambda x: str(x['id']),
        get_excepted_list_id=lambda x: str(x.id),
    ):
        self.assertEqual(
            set([get_current_list_id(item) for item in current_list]),
            set([get_excepted_list_id(item) for item in excepted_list]),
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

    def get_media_url(self, file):
        return f'http://testserver/media/{file}'


class GraphQLSnapShotTestCase(GraphQLTestCase, SnapShotTextCase):
    """
    This TestCase can be used with `self.assertMatchSnapshot`.
    Make sure to only include snapshottests as we are using database flush.
    """
    maxDiff = None
    factories_used = []

    def setUp(self):
        # XXX: This is hacky way to make sure id aren't changed in snapshot. This makes the test slower.
        management.call_command("flush", "--no-input")
        for factory in self.factories_used:
            factory.reset_sequence()
        super().setUp()
        self.now_patcher = patch('django.utils.timezone.now')
        self.now_patcher.start().return_value = datetime.datetime(2021, 1, 1, 0, 0, 0, 123456, tzinfo=pytz.UTC)

    def tearDown(self):
        self.now_patcher.stop()
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
