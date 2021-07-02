import os

from django.conf import settings

from deep.tests import TestCase
from analysis_framework.models import (
    AnalysisFramework,
    AnalysisFrameworkMembership,
)

from project.models import Project
from user.models import User
from organization.models import Organization


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

    def test_get_private_analysis_framework_not_member_but_same_project(self):
        """
        Any member of the project which uses a private framework must be able to see
        the framework.
        """
        private_framework = self.create(AnalysisFramework, is_private=True)
        public_framework = self.create(AnalysisFramework, is_private=False)

        project = self.create(Project, analysis_framework=private_framework)
        # Add self.user to the project, but not to framework
        project.add_member(self.user)

        url = '/api/v1/analysis-frameworks/'
        self.authenticate()
        response = self.client.get(url)

        self.assert_200(response)
        self.assertEqual(len(response.data['results']), 2)
        framework_ids = [x['id'] for x in response.data['results']]
        assert private_framework.id in framework_ids
        assert public_framework.id in framework_ids

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

    def test_get_related_to_me_frameworks(self):
        private_af = self.create(AnalysisFramework, is_private=True)  # noqa
        private_af2 = self.create(AnalysisFramework, is_private=True)

        # The owner role is just a role, what matters is if membership exists or not
        private_af2.add_member(self.user, private_af2.get_or_create_owner_role())

        public_af = self.create(AnalysisFramework, is_private=False)
        public_af.add_member(self.user)
        public_af2 = self.create(AnalysisFramework, is_private=False)  # noqa

        url = '/api/v1/analysis-frameworks/?relatedToMe=true'
        self.authenticate()
        resp = self.client.get(url)
        self.assert_200(resp)
        afs = resp.data['results']

        assert len(afs) == 2, "Two frameworks are related to user"
        af_ids = [x['id'] for x in afs]

        assert private_af2.id in af_ids
        assert public_af.id in af_ids

    def test_get_private_analysis_framework_by_member(self):
        private_framework = self.create(AnalysisFramework, is_private=True)
        public_framework = self.create(AnalysisFramework, is_private=False)

        private_framework.add_member(
            self.user,
            private_framework.get_or_create_owner_role()
        )
        public_framework.add_member(self.user)

        url = '/api/v1/analysis-frameworks/'
        self.authenticate()
        response = self.client.get(url)

        self.assertEqual(len(response.data['results']), 2)
        for framework in response.data['results']:
            assert 'role' in framework
            assert isinstance(framework['role'], dict)

        # Now get a particular private framework
        url = f'/api/v1/analysis-frameworks/{private_framework.id}/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        assert 'role' in response.data
        assert isinstance(response.data['role'], dict)
        self.check_owner_roles_present(private_framework, response.data['role'])

        # Now get a particular public framework, should be 200
        url = f'/api/v1/analysis-frameworks/{public_framework.id}/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        assert 'role' in response.data
        assert isinstance(response.data['role'], dict)
        self.check_default_roles_present(public_framework, response.data['role'])

    def test_get_public_framework_with_roles(self):
        public_framework = self.create(AnalysisFramework, is_private=False)
        url = f'/api/v1/analysis-frameworks/{public_framework.id}/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        assert 'role' in response.data
        assert isinstance(response.data['role'], dict)
        self.check_default_roles_present(public_framework, response.data['role'])

    def test_get_memberships(self):
        framework = self.create(AnalysisFramework)
        framework.add_member(self.user)
        url = f'/api/v1/analysis-frameworks/{framework.id}/memberships/'

        self.authenticate()
        resp = self.client.get(url)

        self.assert_200(resp)
        data = resp.data['results']
        assert len(data) == 1
        assert isinstance(data[0]['member_details'], dict), "Check if member field is expanded"
        assert data[0]['member'] == self.user.id
        assert 'member_details' in data[0]
        assert data[0]['framework'] == framework.id

    def test_get_more_memberships_data(self):
        user1 = self.create_user()
        user2 = self.create_user()
        user3 = self.create_user()
        user4 = self.create_user()
        framework = self.create(AnalysisFramework)
        framework.add_member(
            user=user1,
            role=framework.get_or_create_owner_role(),
            added_by=user2
        )

        url = f'/api/v1/analysis-frameworks/{framework.id}/memberships/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        data = response.data['results']
        assert 'added_by_details' in data[0]
        self.assertEqual(data[0]['added_by_details']['id'], user2.id)
        assert 'role_details' in data[0]

        # test for the pagination support in memberships
        framework.add_member(user2)
        framework.add_member(user3)
        framework.add_member(user4)
        url = f'/api/v1/analysis-frameworks/{framework.id}/memberships/?limit=2'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data['results']), 2)

    def test_create_analysis_framework(self):
        project = self.create(Project, role=self.admin_role)
        organization = self.create(Organization)
        preview_image_sample = os.path.join(settings.BASE_DIR, 'apps/static/image/drop-icon.png')

        url = '/api/v1/analysis-frameworks/'
        data = {
            'title': 'Test AnalysisFramework Title',
            'project': project.id,
            'organization': organization.id,
            'preview_image': open(preview_image_sample, 'rb'),
        }

        self.authenticate()
        response = self.client.post(url, data, format='multipart')
        project.refresh_from_db()
        self.assert_201(response)
        self.assertEqual(response.data['title'], data['title'])
        self.assertEqual(response.data['organization'], data['organization'])
        self.assertEqual(response.data['organization_details']['id'], organization.id)
        self.assertIsNotNone(response.data['preview_image'])
        self.assertEqual(project.analysis_framework_id, response.data['id'])

        # test Group Membership created or not
        assert AnalysisFrameworkMembership.objects.filter(
            framework_id=response.data['id'],
            member=self.user,
            role=project.analysis_framework.get_or_create_owner_role(),
        ).first() is not None, "Membership Should be created"

    def test_clone_analysis_framework_without_name(self):
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
        self.assert_400(response)
        assert 'title' in response.data['errors']

    def test_clone_analysis_framework(self):
        """This is relevant only to public frameworks"""
        analysis_framework = self.create(AnalysisFramework, is_private=False)
        project = self.create(
            Project, analysis_framework=analysis_framework,
            role=self.admin_role
        )
        # Add self.user as member to analysis framework, to check if owner membership created or not
        default_membership, _ = analysis_framework.add_member(self.user)
        # Add owner user, but this should not be in the cloned framework
        user = self.create(User)
        owner_membership, _ = analysis_framework.add_member(user, analysis_framework.get_or_create_owner_role())

        url = '/api/v1/clone-analysis-framework/{}/'.format(
            analysis_framework.id
        )
        cloned_title = 'Cloned AF'
        data = {
            'project': project.id,
            'title': cloned_title,
            'description': 'New Description',
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertNotEqual(response.data['id'], analysis_framework.id)
        self.assertEqual(
            response.data['title'],
            cloned_title)

        project = Project.objects.get(id=project.id)
        new_af = project.analysis_framework

        self.assertNotEqual(new_af.id, analysis_framework.id)
        self.assertEqual(project.analysis_framework.id, response.data['id'])

        # Check if description updated
        assert new_af.description == data['description'], "Description should be updated"
        assert new_af.title == data['title'], "Title should be updated"

        # Test permissions cloned
        # Only the requester should be the owner of the new framework
        assert new_af.members.all().count() == 1, "The cloned framework should have only one owner"
        assert AnalysisFrameworkMembership.objects.filter(
            framework=new_af, role=owner_membership.role,
            member=self.user,
        ).exists()

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
            'title': framework.title[:-12] + '(Modified)',
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

    def test_post_framework_memberships(self):
        user = self.create_user()
        user2 = self.create_user()
        framework = self.create(AnalysisFramework)
        framework.add_member(user, framework.get_or_create_owner_role())

        data = {
            'role': framework.get_or_create_owner_role().id,
            'member': user2.id,
            'framework':framework.id
        }
        self.authenticate(user)
        url = '/api/v1/framework-memberships/'
        response = self.client.post(url, data)
        self.assert_201(response)
        self.assertEqual(response.data['added_by'], user.id)  # set request user to be added_by

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

    def test_search_users_excluding_framework_members(self):
        user1 = self.create(User, email='testuser1@tc.com')
        user2 = self.create(User, email='testuser2@tc.com')
        user3 = self.create(User, email='testuser3@tc.com')

        framework = self.create(AnalysisFramework)
        framework.add_member(user1)

        url = f'/api/v1/users/?members_exclude_framework={framework.id}&search=test'

        self.authenticate()
        resp = self.client.get(url)
        self.assert_200(resp)

        data = resp.data
        ids = [x['id'] for x in data['results']]
        assert user1.id not in ids
        assert user2.id in ids
        assert user3.id in ids

    def test_af_project_api(self):
        framework = self.create(AnalysisFramework, is_private=False)

        self.create_project(is_private=False, analysis_framework=framework, role=None)
        private_project = self.create_project(is_private=True, analysis_framework=framework, role=None)

        url = f'/api/v1/analysis-frameworks/{framework.id}/?fields=all_projects_count,visible_projects'
        self.authenticate(self.user)

        response = self.client.get(url)
        rjson = response.json()
        self.assert_200(response)
        self.assertEqual(rjson['allProjectsCount'], 2)
        self.assertEqual(len(rjson['visibleProjects']), 1)

        # Now add user to the private project
        private_project.add_member(self.user)

        response = self.client.get(url)
        rjson = response.json()
        self.assert_200(response)
        self.assertEqual(rjson['allProjectsCount'], 2)
        self.assertEqual(len(rjson['visibleProjects']), 2)

    def check_owner_roles_present(self, framework, permissions):
        owner_permissions = framework.get_owner_permissions()
        for perm, val in owner_permissions.items():
            assert val == permissions[perm], f'Should match for {perm}'

    def check_default_roles_present(self, framework, permissions):
        default_permissions = framework.get_default_permissions()
        for perm, val in default_permissions.items():
            assert val == permissions[perm], f'Should match for {perm}'

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
