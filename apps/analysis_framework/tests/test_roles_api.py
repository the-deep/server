from deep.tests import TestCase

from analysis_framework.models import AnalysisFramework, Widget
from project.models import Project
from user.models import User


class TestAnalysisFrameworkRoles(TestCase):
    """Test cases for analysis framework roles"""

    def setUp(self):
        super().setUp()

        self.project = self.create(Project, role=self.admin_role)
        # Create private and public frameworks
        self.private_framework = AnalysisFramework.objects.create(
            title='Private Framework',
            project=self.project,
            is_private=True,
        )
        # Create owner role
        self.private_framework.add_member(
            self.user,
            self.private_framework.get_or_create_owner_role()
        )

        self.public_framework = AnalysisFramework.objects.create(
            title='Public Framework',
            project=self.project,
            is_private=False,
            created_by=self.user,
        )
        # Create owner role
        self.private_framework.add_member(
            self.user,
            self.public_framework.get_or_create_owner_role()
        )

        # Add widgets
        self.private_widget = self.create(Widget, analysis_framework=self.private_framework)
        self.public_widget = self.create(Widget, analysis_framework=self.public_framework)

    def test_get_roles(self):
        url = '/api/v1/framework-roles/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

    def test_post_roles(self):
        url = '/api/v1/framework-roles/'
        data = {
            'title': 'Test role',
        }
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_405(response)

    def test_owner_role(self):
        # CLONING THE FRAMEWORK
        response = self._clone_framework_test(self.private_framework)
        self.assert_403(response)

        response = self._clone_framework_test(self.public_framework)
        self.assert_201(response)

        # EDITING THE FRAMEWORK OWNED
        self._edit_framework_test(self.private_framework, self.user, 200)
        self._edit_framework_test(self.public_framework, self.user, 200)

        # Can make the framework public (only to clone)
        self._change_framework_privacy(self.private_framework)
        self._change_framework_privacy(self.public_framework)

        # Can use the framework in other projects

        # ADDING USER and ASSIGNING ROLES
        self._add_user_test(self.public_framework, self.user, 201)
        self._add_user_test(self.private_framework, self.user, 201)

    def test_editor_role(self):
        editor_user = self.create(User)
        self.private_framework.add_member(
            editor_user,
            self.private_framework.get_or_create_editor_role()
        )
        self.public_framework.add_member(
            editor_user,
            self.public_framework.get_or_create_editor_role()
        )

        # CLONING  FRAMEWORK
        response = self._clone_framework_test(self.private_framework, editor_user)
        self.assert_403(response)

        # EDITING FRAMEWORK
        self._edit_framework_test(self.private_framework, editor_user, status=200)
        self._edit_framework_test(self.public_framework, editor_user, status=200)

        # ADDING USER and ASSIGNING ROLES
        self._add_user_test(self.public_framework, editor_user, 403)
        self._add_user_test(self.private_framework, editor_user, 403)

        # Can make the framework public (only to clone)
        self._change_framework_privacy(self.private_framework)
        self._change_framework_privacy(self.public_framework)

    def test_no_role(self):
        normal_user = self.create(User)
        # CLONING  FRAMEWORK
        # private framework
        response = self._clone_framework_test(self.private_framework, normal_user)
        self.assert_403(response)
        # public framework
        response = self._clone_framework_test(self.public_framework, normal_user)
        self.assert_201(response)

        # EDITING FRAMEWORK
        self._edit_framework_test(self.public_framework, normal_user, status=403)
        self._edit_framework_test(self.private_framework, normal_user, status=403)

        # ADDING USER and ASSIGNING ROLES
        self._add_user_test(self.public_framework, normal_user, 403)
        self._add_user_test(self.private_framework, normal_user, 403)

        # Can make the framework public (only to clone)
        self._change_framework_privacy(self.private_framework)
        self._change_framework_privacy(self.public_framework)

    def _edit_framework_test(self, framework, user=None, status=200):
        # Private framework
        edit_data = {
            'title': framework.title + '-edited',
            'is_private': framework.is_private,
            'widgets': []
        }
        self.authenticate(user)
        url = f'/api/v1/analysis-frameworks/{framework.id}/'
        response = self.client.put(url, edit_data)
        self.assertEqual(response.status_code, status)

    def _clone_framework_test(self, framework, user=None):
        clone_url = f'/api/v1/clone-analysis-framework/{framework.id}/'
        self.authenticate(user)
        return self.client.post(clone_url)

    def _add_user_test(self, framework, user, status=201):
        add_user_url = f'/api/v1/framework-memberships/'
        new_user = self.create(User)
        add_member_data = {
            'framework': self.private_framework.id,
            'member': new_user.id,
            'role': framework.get_or_create_editor_role().id,  # Just an arbritrary role
        }
        self.authenticate(user)
        response = self.client.post(add_user_url, add_member_data)
        self.assertEqual(response.status_code, status)

    def _change_framework_privacy(self, framework):
        url = f'/api/v1/analysis-frameworks/{framework.id}/'

        changed_privacy = not framework.is_private
        put_data = {
            'title': framework.title,
            'is_private': changed_privacy,
            # Other fields we don't care
        }
        self.authenticate()
        response = self.client.put(url, put_data)
        self.assert_403(response)

        # Try patching, should give 403 as well
        patch_data = {'is_private': changed_privacy}
        response = self.client.patch(url, patch_data)
        self.assert_403(response)

        # Try patching other field, should give 200
        patch_data = {'title': 'Patched title'}
        response = self.client.patch(url, patch_data)
        self.assert_200(response)

        # Try modifying other values, should give 200
        put_data = {
            'title': framework.title + '(Modified)',
            'is_private': framework.is_private,
        }
        response = self.client.put(url, put_data)
        self.assert_200(response)

    def _use_framework_in_other_projects_test(self, framework, project):
        # TODO: implement this
        pass
