from deep.tests import TestCase
from analysis_framework.models import (
    AnalysisFramework,
    AnalysisFrameworkMembership,
)

from project.models import Project


class AnalysisFrameworkTests(TestCase):

    def test_get_private_analysis_framework_not_member(self):
        private_framework = self.create(AnalysisFramework, is_private=True)
        public_framework = self.create(AnalysisFramework, is_private=False)

        url = '/api/v1/analysis-frameworks/'
        self.authenticate()
        response = self.client.get(url)

        self.assert_200(response)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], public_framework.id)

        # Now get a particular private framework
        url = f'/api/v1/analysis-frameworks/{private_framework.id}/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_404(response)

        # Now get a particular public framework, should be 200
        url = f'/api/v1/analysis-frameworks/{public_framework.id}/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

    def test_get_private_analysis_framework_by_member(self):
        private_framework = self.create(AnalysisFramework, is_private=True)
        public_framework = self.create(AnalysisFramework, is_private=False)

        private_framework.add_member(self.user)

        url = '/api/v1/analysis-frameworks/'
        self.authenticate()
        response = self.client.get(url)

        self.assertEqual(len(response.data['results']), 2)

        # Now get a particular private framework
        url = f'/api/v1/analysis-frameworks/{private_framework.id}/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        # Now get a particular public framework, should be 200
        url = f'/api/v1/analysis-frameworks/{public_framework.id}/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

    def test_create_analysis_framework(self):
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/analysis-frameworks/'
        data = {
            'title': 'Test AnalysisFramework Title',
            'project': project.id,
        }

        response = self.post_and_check_201(url, data, AnalysisFramework, ['title'])

        project = Project.objects.get(id=project.id)
        self.assertEqual(project.analysis_framework.id, response.data['id'])

        # test Group Membership created or not
        assert AnalysisFrameworkMembership.objects.filter(
            framework_id=response.data['id'],
            member=self.user,
            role=project.analysis_framework.get_or_create_owner_role(),
        ).first() is not None, "Membership Should be created"

    def test_clone_analysis_framework(self):
        analysis_framework = self.create(AnalysisFramework)
        project = self.create(
            Project, analysis_framework=analysis_framework,
            role=self.admin_role
        )

        url = '/api/v1/clone-analysis-framework/{}/'.format(
            analysis_framework.id
        )
        data = {
            'project': project.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertNotEqual(response.data['id'], analysis_framework.id)
        self.assertEqual(
            response.data['title'],
            analysis_framework.title[:230] + ' (cloned)')

        project = Project.objects.get(id=project.id)
        self.assertNotEqual(project.analysis_framework.id,
                            analysis_framework.id)

        self.assertEqual(project.analysis_framework.id, response.data['id'])

    def test_create_private_framework_unauthorized(self):
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/analysis-frameworks/'
        data = {
            'title': 'Test AnalysisFramework Title',
            'project': project.id,
            'is_private': True,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_403(response)

    def test_create_private_framework(self):
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/analysis-frameworks/'
        data = {
            'title': 'Test AnalysisFramework Title',
            'project': project.id,
            'is_private': True,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_403(response)

    def test_change_is_private_field(self):
        """Even the owner should be unable to change privacy"""
        private_framework = self.create(AnalysisFramework, is_private=True)
        public_framework = self.create(AnalysisFramework, is_private=False)
        private_framework.add_member(
            self.user,
            private_framework.get_or_create_owner_role()
        )
        public_framework.add_member(
            self.user,
            public_framework.get_or_create_owner_role()
        )
        self._change_framework_privacy(public_framework, 403)
        self._change_framework_privacy(private_framework, 403)

    def test_change_other_fields(self):
        # Try modifying other values, should give 200
        framework = self.create(AnalysisFramework)
        framework.add_member(self.user, framework.get_or_create_owner_role())

        url = f'/api/v1/analysis-frameworks/{framework.id}/'
        put_data = {
            'title': framework.title + '(Modified)',
            'is_private': framework.is_private,
        }
        self.authenticate()
        response = self.client.put(url, put_data)
        self.assert_200(response)

    def test_get_membersips(self):
        url = '/api/v1/framework-memberships/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        for membership in response.data['results']:
            self.assertEqual(membership['member'], self.user.id)

    def test_add_roles_to_public_framework_non_member(self):
        framework = self.create(AnalysisFramework, is_private=False)
        add_member_data = {
            'framework': framework.id,
            'member': self.user.id,
            'role': framework.get_or_create_editor_role().id,  # Just an arbritrary role
        }
        self.authenticate()
        url = '/api/v1/framework-memberships/'
        response = self.client.post(url, add_member_data)
        self.assert_403(response)

    def test_project_analysis_framework(self):
        analysis_framework = self.create(AnalysisFramework)
        project = self.create(
            Project, analysis_framework=analysis_framework,
            role=self.admin_role
        )

        url = '/api/v1/projects/{}/analysis-framework/'.format(
            project.id
        )

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['id'], analysis_framework.id)
        self.assertEqual(response.data['title'], analysis_framework.title)

    def test_filter_analysis_framework(self):
        url = '/api/v1/analysis-frameworks/'
        self.authenticate()
        response = self.client.get(f'{url}?activity=active&relatedToMe=True')
        self.assert_200(response)

    def _change_framework_privacy(self, framework, status=403, user=None):
        url = f'/api/v1/analysis-frameworks/{framework.id}/'

        changed_privacy = not framework.is_private
        put_data = {
            'title': framework.title,
            'is_private': changed_privacy,
            # Other fields we don't care
        }
        self.authenticate(user)
        response = self.client.put(url, put_data)
        self.assertEqual(response.status_code, status)

        # Try patching, should give 403 as well
        patch_data = {'is_private': changed_privacy}
        response = self.client.patch(url, patch_data)
        self.assertEqual(response.status_code, status)
