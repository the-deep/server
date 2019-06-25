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
        # Can use the framework in other projects
        # Can add users and assign roles

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

    def _edit_framework_test(self, framework, user=None, status=201):
        # Private framework
        edit_data = {
            'title': framework.title + '-edited',
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

    def _add_user(self, framework, user):
        pass

    def _make_framework_public(self, framework):
        pass

    def _edit_framework(self, framework):
        pass

    def _use_framework_in_other_projects(self, framework, project):
        pass
