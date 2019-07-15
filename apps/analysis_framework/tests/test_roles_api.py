from deep.tests import TestCase

from analysis_framework.models import (
    AnalysisFramework, Widget,
    AnalysisFrameworkMembership,
)
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
        self.public_framework = AnalysisFramework.objects.create(
            title='Public Framework',
            project=self.project,
            is_private=False,
            created_by=self.user,
        )
        # Add widgets
        self.private_widget = self.create(Widget, analysis_framework=self.private_framework)
        self.public_widget = self.create(Widget, analysis_framework=self.public_framework)

    def test_get_private_roles(self):
        url = '/api/v1/private-framework-roles/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        data = response.data
        for role in data['results']:
            assert role['is_private_role'] is True, "Must be a private role"

    def test_get_public_roles(self):
        url = '/api/v1/private-framework-roles/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        data = response.data
        for role in data['results']:
            assert role['is_private_role'] is not True, "Must be a public role"

    def test_owner_role(self):
        self.private_framework.add_member(
            self.user,
            self.private_framework.get_or_create_owner_role()
        )
        self.public_framework.add_member(
            self.user,
            self.public_framework.get_or_create_owner_role()
        )
        # CLONING THE FRAMEWORK
        response = self._clone_framework_test(self.private_framework)
        self.assert_403(response)

        response = self._clone_framework_test(self.public_framework)
        self.assert_201(response)

        # EDITING THE FRAMEWORK OWNED
        self._edit_framework_test(self.private_framework, self.user, 200)
        self._edit_framework_test(self.public_framework, self.user, 200)

        # Can use the framework in other projects

        self._add_user_test(self.public_framework, self.user, 201)
        self._add_user_test(self.private_framework, self.user, 201)

    def test_patch_membership(self):
        self.private_framework.add_member(
            self.user,
            self.private_framework.get_or_create_owner_role(),
        )
        editor = self.private_framework.get_or_create_editor_role()
        user = self.create(User)
        membership, _ = self.private_framework.add_member(user)

        url = f'/api/v1/framework-memberships/{membership.id}/'

        patch_data = {
            'role': editor.id,
        }

        self.authenticate()
        resp = self.client.patch(url, patch_data)

        self.assert_200(resp)

    def test_get_membership(self):
        self.private_framework.add_member(
            self.user,
            self.private_framework.get_or_create_owner_role(),
        )
        user = self.create(User)
        membership, _ = self.private_framework.add_member(user)

        url = f'/api/v1/framework-memberships/{membership.id}/'

        self.authenticate()
        resp = self.client.get(url)

        self.assert_200(resp)

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
        self._edit_framework_test(self.private_framework, normal_user, status=404)

        # ADDING USER and ASSIGNING ROLES
        self._add_user_test(self.public_framework, normal_user, 403)
        self._add_user_test(self.private_framework, normal_user, 404)

    def test_add_user_with_public_role_to_private_framework(self):
        private_framework = self.create(AnalysisFramework, is_private=True)
        public_framework = self.create(AnalysisFramework, is_private=False)
        user = self.create(User)
        # A public role will be assigned to the user
        public_role = public_framework.get_or_create_editor_role()
        private_framework.add_member(self.user, private_framework.get_or_create_owner_role())

        url = '/api/v1/framework-memberships/'
        post_data = {
            'framework': private_framework.id,
            'member': user.id,
            'role': public_role.id
        }
        self.authenticate()
        resp = self.client.post(url, post_data)
        self.assert_403(resp)

    def test_add_user_with_private_role_to_public_framework(self):
        private_framework = self.create(AnalysisFramework, is_private=True)
        public_framework = self.create(AnalysisFramework, is_private=False)
        user = self.create(User)
        # A private role will be assigned to the user
        private_role = private_framework.get_or_create_editor_role()
        public_framework.add_member(self.user, public_framework.get_or_create_owner_role())

        url = '/api/v1/framework-memberships/'
        post_data = {
            'framework': public_framework.id,
            'member': user.id,
            'role': private_role.id
        }
        self.authenticate()
        resp = self.client.post(url, post_data)
        self.assert_403(resp)

    def test_default_role_private_framework(self):
        """When not sent role field, default role will be added"""
        private_framework = self.create(AnalysisFramework, is_private=True)
        user = self.create(User)
        private_framework.add_member(self.user, private_framework.get_or_create_owner_role())

        url = '/api/v1/framework-memberships/'
        post_data = {
            'framework': private_framework.id,
            'member': user.id,
        }
        self.authenticate()
        resp = self.client.post(url, post_data)
        self.assert_201(resp)

        # Now check if user has default_role
        memship = AnalysisFrameworkMembership.objects.filter(
            member=user, framework=private_framework,
        ).first()

        assert memship is not None, "Membership should be created"
        permissions = memship.role.permissions
        assert permissions == private_framework.get_default_permissions(), \
            "The permissions should be the default permissions"

    def test_default_role_public_framework(self):
        """When not sent role field, default role will be added"""
        public_framework = self.create(AnalysisFramework, is_private=False)
        user = self.create(User)
        public_framework.add_member(self.user, public_framework.get_or_create_owner_role())

        url = '/api/v1/framework-memberships/'
        post_data = {
            'framework': public_framework.id,
            'member': user.id,
        }
        self.authenticate()
        resp = self.client.post(url, post_data)
        self.assert_201(resp)

        # Now check if user has default_role
        memship = AnalysisFrameworkMembership.objects.filter(
            member=user, framework=public_framework,
        ).first()

        assert memship is not None, "Membership should be created"
        permissions = memship.role.permissions
        assert permissions == public_framework.get_default_permissions(), \
            "The permissions should be the default permissions"

    def test_owner_cannot_delete_himself(self):
        framework = self.create(AnalysisFramework)
        owner_role = framework.get_or_create_owner_role()
        membership, _ = framework.add_member(self.user, owner_role)

        url = f'/api/v1/framework-memberships/{membership.id}/'

        self.authenticate()
        resp = self.client.delete(url)
        self.assert_403(resp)

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

    def _add_user_test(self, framework, user, status=201, role=None):
        add_user_url = f'/api/v1/framework-memberships/'
        role = (role and role.id) or framework.get_or_create_editor_role().id,
        new_user = self.create(User)
        add_member_data = {
            'framework': framework.id,
            'member': new_user.id,
            'role': framework.get_or_create_editor_role().id,  # Just an arbritrary role
        }
        self.authenticate(user)
        response = self.client.post(add_user_url, add_member_data)
        self.assertEqual(response.status_code, status)
