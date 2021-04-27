import uuid

from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.utils.hashable import make_hashable

from user.models import (
    User,
    Feature,
)
from deep.tests import TestCase
from entry.models import (
    Lead,
    Entry,
    Attribute,
    EntryComment,
    EntryCommentText,
)
from analysis_framework.models import (
    AnalysisFramework,
    AnalysisFrameworkRole,
    Widget,
)
from lead.models import LeadGroup
from project.tasks import (
    _generate_project_viz_stats,
    _generate_project_stats_cache,
)
from ary.models import AssessmentTemplate
from project.models import (
    Project,
    ProjectRole,
    ProjectMembership,
    ProjectJoinRequest,
    ProjectUserGroupMembership,
    ProjectOrganization,
    ProjectStats,
)

from organization.models import (
    Organization
)

from user_group.models import UserGroup

from . import entry_stats_data


# TODO Document properly some of the following complex tests


class ProjectApiTest(TestCase):
    fixtures = ['ary_template_data.json']

    def setUp(self):
        super().setUp()
        # create some users
        self.user1 = self.create(User)
        self.user2 = self.create(User)
        self.user3 = self.create(User)
        # and some user groups
        self.ug1 = self.create(UserGroup, role='admin')
        self.ug1.add_member(self.user1)
        self.ug1.add_member(self.user2)
        self.ug2 = self.create(UserGroup, role='admin')
        self.ug2.add_member(self.user2)
        self.ug2.add_member(self.user3)
        self.org1 = self.create(Organization, title='Test Organization')

    def test_create_project(self):
        project_count = Project.objects.count()

        url = '/api/v1/projects/'
        data = {
            'title': 'Test project',
            'data': {'testKey': 'testValue'},
            'organizations': [
                {'organization': self.org1.id, 'organization_type': ProjectOrganization.DONOR},
            ],
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Project.objects.count(), project_count + 1)
        self.assertEqual(response.data['title'], data['title'])

    def test_check_assessment_template_in_project_create(self):
        project_count = Project.objects.count()
        assessment = self.create(AssessmentTemplate)
        url = '/api/v1/projects/'
        data = {
            'title': 'Test project',
            'data': {'testKey': 'testValue'},
            'organizations': [
                {'organization': self.org1.id, 'organization_type': ProjectOrganization.DONOR},
            ],
            'has_assessments': True
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Project.objects.count(), project_count + 1)
        self.assertEqual(response.data['assessment_template'], assessment.id)

        # providing `has_assessments=False`
        data['has_assessments'] = False
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)
        self.assertNotIn('assessment_template', response.data)

        # providing `has_assessments=None`
        data['has_assessments'] = None
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_400(response)

    def create_project_api(self, **kwargs):
        url = '/api/v1/projects/'
        data = {
            'title': kwargs.get('title'),
            'is_private': kwargs.get('is_private'),
            'organizations': kwargs.get('organizations', [])
        }

        response = self.client.post(url, data)
        return response

    def test_get_projects(self):
        user_fhx = self.create(User)
        self.create(Feature, feature_type=Feature.GENERAL_ACCESS,
                    key=Feature.PRIVATE_PROJECT, title='Private project',
                    users=[user_fhx], email_domains=[])
        self.authenticate(user_fhx)

        self.create_project_api(title='Project 1', is_private=False)
        self.create_project_api(title='Project 2', is_private=False)
        self.create_project_api(title='Project 3', is_private=False)
        self.create_project_api(title='Project 4', is_private=False)
        self.create_project_api(title='Private Project 1', is_private=True)

        response = self.client.get('/api/v1/projects/')
        self.assertEqual(len(response.data['results']), 5)

        other_user = self.create(User)
        self.authenticate(other_user)

        # self.create_project_api(title='Project 5', is_private=False)
        # self.create_project_api(title='Private Project 3', is_private=True)

        response = self.client.get('/api/v1/projects/')
        self.assertEqual(len(response.data['results']), 4)

    def test_get_project_members(self):
        user1 = self.create(User)
        user2 = self.create(User)

        # Create usergroup and add members
        usergroup = self.create(UserGroup)
        userg1 = self.create(User)
        userg2 = self.create(User)

        usergroup.add_member(userg1)
        usergroup.add_member(userg2)

        project = self.create(Project)

        project.add_member(user1)
        ProjectUserGroupMembership.objects.create(project=project, usergroup=usergroup)

        url = f'/api/v1/projects/{project.id}/members/'

        self.authenticate(user1)  # autheniticate with the members only
        resp = self.client.get(url)
        self.assert_200(resp)

        userids = [x['id'] for x in resp.data['results']]
        assert user1.id in userids
        assert user2.id not in userids
        assert userg1.id in userids
        assert userg2.id in userids
        assert len(userids) == 3, "Three members"

    def test_create_private_project(self):
        # project_count = Project.objects.count()
        url = '/api/v1/projects/'
        data = {
            'title': 'Test private project',
            'is_private': 'true',
            'organizations': [],
        }

        user_fhx = self.create(User, email='fhx@togglecorp.com')
        self.create(Feature, feature_type=Feature.GENERAL_ACCESS,
                    key=Feature.PRIVATE_PROJECT, title='Private project',
                    users=[user_fhx], email_domains=[])

        self.authenticate(user_fhx)
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(response.data['is_private'], True)
        self.assertEqual(Project.objects.last().is_private, True)

    def test_change_private_project_to_public(self):
        private_project = self.create(Project, is_private=True, organizations=[])
        public_project = self.create(Project, is_private=False, organizations=[])

        # Add roles for self.user
        private_project.add_member(self.user, ProjectRole.get_creator_role())
        public_project.add_member(self.user, ProjectRole.get_creator_role())

        self._change_project_privacy_test(private_project, 403, self.user)
        self._change_project_privacy_test(public_project, 403, self.user)

    def test_create_private_project_unauthorized(self):
        user_fhx = self.create(User, email='fhx@togglecorp.com')
        user_dummy = self.create(User, email='dummy@test.com')

        self.create(Feature, feature_type=Feature.GENERAL_ACCESS,
                    key=Feature.PRIVATE_PROJECT, title='Private project',
                    users=[user_dummy], email_domains=[])

        self.authenticate(user_fhx)
        self.assert_403(self.create_project_api(title='Private test', is_private=True))

        self.authenticate(user_dummy)
        self.assert_201(self.create_project_api(title='Private test', is_private=True))

    def test_get_private_project_detail_unauthorized(self):
        user_fhx = self.create(User, email='fhx@togglecorp.com')
        self.create(Feature, feature_type=Feature.GENERAL_ACCESS,
                    key=Feature.PRIVATE_PROJECT, title='Private project',
                    users=[user_fhx], email_domains=[])

        self.authenticate(user_fhx)
        response = self.create_project_api(title='Test private project', is_private=True)
        self.assert_201(response)

        self.assertEqual(response.data['is_private'], True)
        self.assertEqual(Project.objects.last().is_private, True)

        other_user = self.create(User)
        self.authenticate(other_user)

        new_private_project_id = response.data['id']
        response = self.client.get(f'/api/v1/projects/{new_private_project_id}/')

        self.assert_404(response)

    def test_private_project_use_public_framework(self):
        """Can use public framework"""
        private_project = self.create(Project, is_private=True, organizations=[])
        public_framework = self.create(AnalysisFramework, is_private=False)

        private_project.add_member(
            self.user,
            # Test with role which can modify project
            ProjectRole.get_creator_role(),
        )

        url = f'/api/v1/projects/{private_project.id}/'
        data = {
            'title': private_project.title,
            'analysis_framework': public_framework.id,
            'organizations': [],
            # ... don't care other fields
        }
        self.authenticate()
        response = self.client.put(url, data)
        self.assert_200(response)

    def test_private_project_use_private_framework_if_framework_member(self):
        """Can use private framework if member of framework"""
        private_project = self.create(Project, is_private=True, organizations=[])
        private_framework = self.create(AnalysisFramework, is_private=False)

        private_framework.add_member(
            self.user,
            private_framework.get_or_create_default_role()
        )

        private_project.add_member(
            self.user,
            # Test with role which can modify project
            ProjectRole.get_creator_role(),
        )

        url = f'/api/v1/projects/{private_project.id}/'
        data = {
            'title': private_project.title,
            'analysis_framework': private_framework.id,
            'organizations': [],
            # ... don't care other fields
        }
        self.authenticate()
        response = self.client.put(url, data)
        self.assert_200(response)

    def test_private_project_use_private_framework_if_not_framework_member(self):
        """Can't use private framework if not member of framework"""
        private_project = self.create(Project, is_private=True, organizations=[])
        private_framework = self.create(AnalysisFramework, is_private=True)

        private_project.add_member(
            self.user,
            # Test with role which can modify project
            ProjectRole.get_creator_role(),
        )

        url = f'/api/v1/projects/{private_project.id}/'
        data = {
            'title': private_project.title,
            'analysis_framework': private_framework.id,
            'organizations': [],
            # ... don't care other fields
        }
        self.authenticate()
        response = self.client.put(url, data)
        # Framework should not be visible if not member,
        # Just send bad request
        self.assert_400(response)

    def test_private_project_use_private_framework_if_framework_member_no_can_use(self):
        """Can't use private framework if member of framework but no can_use permission"""
        private_project = self.create(Project, is_private=True, organizations=[])
        private_framework = self.create(AnalysisFramework, is_private=True)

        framework_role_no_permissions = AnalysisFrameworkRole.objects.create()
        private_framework.add_member(
            self.user,
            framework_role_no_permissions
        )

        private_project.add_member(
            self.user,
            # Test with role which can modify project
            ProjectRole.get_creator_role(),
        )

        url = f'/api/v1/projects/{private_project.id}/'
        data = {
            'title': private_project.title,
            'analysis_framework': private_framework.id,
            'organizations': [],
            # ... don't care other fields
        }
        self.authenticate()
        response = self.client.put(url, data)
        # Framework should be visible if member,
        # but forbidden if not permission to use in other projects
        self.assert_403(response)

    def test_public_project_use_public_framework(self):
        """Can use public framework"""
        public_project = self.create(Project, is_private=False)
        public_framework = self.create(AnalysisFramework, is_private=False)

        public_project.add_member(
            self.user,
            # Test with role which can modify project
            ProjectRole.get_creator_role(),
        )

        url = f'/api/v1/projects/{public_project.id}/'
        data = {
            'title': public_project.title,
            'analysis_framework': public_framework.id,
            'organizations': [],
            # ... don't care other fields
        }
        self.authenticate()
        response = self.client.put(url, data)
        self.assert_200(response)

    def test_public_project_use_private_framework(self):
        """Can't use private framework even if member"""
        public_project = self.create(Project, is_private=False, organizations=[])
        private_framework = self.create(AnalysisFramework, is_private=True)

        public_project.add_member(
            self.user,
            # Test with role which can modify project
            ProjectRole.get_creator_role(),
        )
        private_framework.add_member(
            self.user,
            private_framework.get_or_create_owner_role(),  # Any role will work which
            # has can_use_in_other_projects True
        )

        url = f'/api/v1/projects/{public_project.id}/'
        data = {
            'title': public_project.title,
            'analysis_framework': private_framework.id,
            'organizations': [],
            # ... don't care other fields
        }
        self.authenticate()
        response = self.client.put(url, data)
        self.assert_403(response)

    def test_project_get_with_user_group_field(self):
        # TODO: can make this more generic for other fields as well
        project = self.create(
            Project,
            user_groups=[],
            title='TestProject',
            role=self.admin_role,
            organizations=[]
        )
        # Add usergroup
        ProjectUserGroupMembership.objects.create(
            usergroup=self.ug1,
            project=project
        )
        # Now get project and validate fields
        url = '/api/v1/projects/{}/'.format(project.pk)
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        project = response.json()
        assert 'id' in project
        assert 'userGroups' in project
        assert len(project['userGroups']) > 0
        for ug in project['userGroups']:
            assert isinstance(ug, dict)
            assert 'id' in ug
            assert 'title' in ug

    def test_update_project_organizations(self):
        org1 = self.create(Organization, title='Test Organization 1')
        org2 = self.create(Organization, title='Test Organization 2')
        org3 = self.create(Organization, title='Test Organization 3')
        org4 = self.create(Organization, title='Test Organization 4')
        org5 = self.create(Organization, title='Test Organization 5')

        url = '/api/v1/projects/'
        data = {
            'title': 'TestProject',
            'organizations': [
                {'organization': org1.id, 'organization_type': ProjectOrganization.DONOR},
                {'organization': org2.id, 'organization_type': ProjectOrganization.GOVERNMENT},
                {'organization': org3.id, 'organization_type': ProjectOrganization.GOVERNMENT},
            ],
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        url = '/api/v1/projects/{}/'.format(response.json()['id'])

        data = {
            'organizations': [
                {'organization': org4.id, 'organization_type': ProjectOrganization.DONOR},
                {'organization': org5.id, 'organizatino_type': ProjectOrganization.GOVERNMENT},
            ],
        }

        response = self.client.patch(url, data)
        self.assert_200(response)

        assert len(response.json()['organizations']) == 2

    def test_update_project_add_user_group(self):
        project = self.create(
            Project,
            user_groups=[],
            title='TestProject',
            role=self.admin_role
        )
        memberships = ProjectMembership.objects.filter(project=project)
        initial_member_count = memberships.count()

        url = f'/api/v1/projects/{project.id}/project-usergroups/'
        data = {
            'usergroup': self.ug1.id,
            'role': self.normal_role.id
        }

        self.authenticate()
        response = self.client.post(url, data)
        assert response.status_code == 201

        final_memberships = ProjectMembership.objects.filter(project=project)
        final_member_count = final_memberships.count()
        # now check for members
        self.assertEqual(
            initial_member_count + self.ug1.members.all().count() - 1,
            # -1 because usergroup admin and project admin is common
            final_member_count
        )
        self.assertEqual(response.data['role_details']['title'], self.normal_role.title)
        self.assertEqual(response.data['project'], project.id)

    def test_update_project_remove_ug(self):
        project = self.create(
            Project,
            title='TestProject',
            user_groups=[],
            role=self.admin_role
        )
        # Add usergroups
        ProjectUserGroupMembership.objects.create(
            usergroup=self.ug1,
            project=project
        )
        project_ug2 = ProjectUserGroupMembership.objects.create(
            usergroup=self.ug2,
            project=project
        )

        initial_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()

        # We keep just ug1, and remove ug2
        url = f'/api/v1/projects/{project.id}/project-usergroups/{project_ug2.id}/'

        self.authenticate()
        response = self.client.delete(url)
        self.assert_204(response)

        final_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()

        # now check for members
        self.assertEqual(
            # Subtract all members from second group except
            # the two users that are common in both user groups
            initial_member_count - self.ug2.members.all().count() + 2,
            final_member_count
        )

    def test_add_user_to_usergroup(self):
        project = self.create(
            Project,
            title='TestProject',
            user_groups=[],
            role=self.admin_role
        )
        # Add usergroups
        project_ug1 = ProjectUserGroupMembership.objects.create(
            usergroup=self.ug1,
            project=project
        )
        initial_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()
        # Create a new user and add it to project_ug1
        newUser = self.create(User)

        from user_group.models import GroupMembership
        GroupMembership.objects.create(
            member=newUser,
            group=project_ug1.usergroup
        )
        final_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()
        self.assertEqual(initial_member_count + 1, final_member_count)

    def test_remove_user_in_only_one_usergroup(self):
        project = self.create(
            Project,
            title='TestProject',
            user_groups=[],
            role=self.admin_role
        )
        # Add usergroups
        project_ug1 = ProjectUserGroupMembership.objects.create(
            usergroup=self.ug1,
            project=project
        )

        initial_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()

        from user_group.models import GroupMembership

        GroupMembership.objects.filter(
            member=self.user1,  # user1 belongs to ug1
            group=project_ug1.usergroup
        ).delete()

        final_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()
        self.assertEqual(initial_member_count - 1, final_member_count)

    def test_remove_user_in_only_multiple_usergroups(self):
        project = self.create(
            Project,
            title='TestProject',
            user_groups=[],
            role=self.admin_role
        )

        # Add usergroups
        project_ug1 = ProjectUserGroupMembership.objects.create(
            usergroup=self.ug1,
            project=project
        )
        ProjectUserGroupMembership.objects.create(
            usergroup=self.ug2,
            project=project
        )

        initial_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()

        from user_group.models import GroupMembership

        GroupMembership.objects.filter(
            member=self.user2,  # user1 belongs to ug1 and ug2
            group=project_ug1.usergroup
        ).delete()

        final_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()
        # Should be no change in membeship as user2 is member from ug2 as well
        self.assertEqual(initial_member_count, final_member_count)

    def test_member_of(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)

        url = '/api/v1/projects/member-of/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], project.id)

        url = '/api/v1/projects/member-of/?user={}'.format(test_user.id)

        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 0)

    def test_project_of_user(self):
        test_user = self.create(User)

        url = '/api/v1/projects/member-of/?user={}'.format(test_user.id)
        self.authenticate()

        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 0)

        url = '/api/v1/projects/member-of/'
        # authenticate test_user
        self.authenticate(test_user)
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 0)

        # Create another project and add test_user to the project
        project1 = self.create(Project, role=self.admin_role)
        project1.add_member(test_user)

        # authenticate test_user
        self.authenticate(test_user)
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], project1.id)

    def test_project_members_view(self):
        # NOTE: Can only get if  member of project
        project1 = self.create(Project)
        test_user = self.create(User)
        test_dummy = self.create(User)
        project1.add_member(test_user, role=self.admin_role)

        url = f'/api/v1/projects/{project1.pk}/members/'
        # authenticate test_user
        self.authenticate(test_user)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data['count'], 1)

        # authenticate test_dummy user
        self.authenticate(test_dummy)
        response = self.client.get(url)
        self.assert_403(response)

    def test_add_member(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)

        url = f'/api/v1/projects/{project.id}/project-memberships/'
        data = {
            'member': test_user.pk,
            'role': self.normal_role.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(response.data['role'], data['role'])
        self.assertEqual(response.data['member'], data['member'])
        self.assertEqual(response.data['project'], project.id)
        self.assertEqual(response.data['role_details']['title'], self.normal_role.title)

    def test_add_member_unexistent_role(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)

        url = f'/api/v1/projects/{project.id}/project-memberships/'
        data = {
            'member': test_user.pk,
            'role': 9999
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_400(response)
        assert 'errors' in response.data

    def test_add_member_duplicate(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        project.add_member(test_user)

        url = f'/api/v1/projects/{project.id}/project-memberships/'
        data = {
            'member': test_user.pk
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_400(response)
        assert 'errors' in response.data
        assert 'member' in response.data['errors']

    def test_project_membership_edit_normal_role(self):
        # user try to update member where he/she isnot the admin in the project
        project = self.create(Project, role=self.normal_role)  # this creates user with normal_role
        test_user = self.create(User)
        m1 = project.add_member(test_user, role=self.normal_role)
        data = {
            'role': self.admin_role.id,
        }
        url = f'/api/v1/projects/{project.id}/project-memberships/{m1.id}/'
        self.authenticate()  # authenticate with normal_role
        response = self.client.patch(url, data)
        self.assert_403(response)

    def test_project_membership_edit_admin_role(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        m1 = project.add_member(test_user, role=self.normal_role)
        data = {
            'role': self.admin_role.id
        }
        url = f'/api/v1/projects/{project.id}/project-memberships/{m1.id}/'
        self.authenticate()  # authenticate with admin_role
        response = self.client.patch(url, data)
        self.assert_200(response)

    def test_project_membership_add(self):
        # user try to add member where he/she isnot the admin in the project
        project = self.create(Project)
        test_user1 = self.create(User)
        test_user2 = self.create(User)
        project.add_member(test_user2, role=self.normal_role)
        data = {
            'member': test_user1.id,
            'role': self.admin_role.id
        }
        url = f'/api/v1/projects/{project.id}/project-memberships/'
        self.authenticate(test_user2)  # test_user2 has normal_role in project
        response = self.client.post(url, data)
        self.assert_400(response)

    def test_options(self):
        url = '/api/v1/project-options/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

    def test_project_status_in_project_options(self):
        choices = dict(make_hashable(Project.STATUS_CHOICES))

        url = '/api/v1/project-options/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        self.assertIn('project_status', response.data)
        self.assertEqual(response.data['project_status'][0]['key'], Project.ACTIVE)
        self.assertEqual(response.data['project_status'][0]['value'], choices[Project.ACTIVE])
        self.assertEqual(response.data['project_status'][1]['key'], Project.INACTIVE)
        self.assertEqual(response.data['project_status'][1]['value'], choices[Project.INACTIVE])

    def test_join_request(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        data = dict(
            reason='bla',
        )

        url = '/api/v1/projects/{}/join/'.format(project.id)

        self.authenticate(test_user)
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(response.data['project']['id'], project.id)
        self.assertEqual(response.data['requested_by']['id'], test_user.id)
        self.assertEqual(
            ProjectJoinRequest.objects.get(id=response.data['id']).data['reason'],
            data['reason']
        )

    def test_invalid_join_request(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        url = '/api/v1/projects/{}/join/'.format(project.id)

        self.authenticate(test_user)
        response = self.client.post(url)
        self.assert_400(response)
        self.assertIn('reason', response.data['errors'])

    def test_accept_request(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=test_user,
            role=self.admin_role
        )

        url = '/api/v1/projects/{}/requests/{}/accept/'.format(
            project.id,
            request.id,
        )

        self.authenticate()
        response = self.client.post(url)
        self.assert_200(response)

        self.assertEqual(response.data['responded_by']['id'], self.user.id)
        self.assertEqual(response.data['status'], 'accepted')
        membership = ProjectMembership.objects.filter(
            project=project,
            member=test_user,
            role=self.normal_role,
        )
        self.assertEqual(membership.count(), 1)

    def test_reject_request(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=test_user,
            role=self.admin_role
        )

        url = '/api/v1/projects/{}/requests/{}/reject/'.format(
            project.id,
            request.id,
        )

        self.authenticate()
        response = self.client.post(url)
        self.assert_200(response)

        self.assertEqual(response.data['responded_by']['id'], self.user.id)
        self.assertEqual(response.data['status'], 'rejected')
        membership = ProjectMembership.objects.filter(
            project=project,
            member=test_user,
            role=self.normal_role
        )
        self.assertEqual(membership.count(), 0)

    def test_cancel_request(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=test_user,
            role=self.admin_role
        )

        url = '/api/v1/projects/{}/join/cancel/'.format(project.id)

        self.authenticate(test_user)
        response = self.client.post(url)
        self.assert_204(response)

        request = ProjectJoinRequest.objects.filter(id=request.id)
        self.assertEqual(request.count(), 0)

    def test_list_request(self):
        project = self.create(Project, role=self.admin_role)
        self.create(ProjectJoinRequest, project=project)
        self.create(ProjectJoinRequest, project=project)
        self.create(ProjectJoinRequest, project=project)

        url = '/api/v1/projects/{}/requests/'.format(project.id)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['count'], 3)

    def test_delete_project_admin(self):
        project = self.create(Project, role=self.admin_role)
        url = '/api/v1/projects/{}/'.format(project.id)
        self.authenticate()
        response = self.client.delete(url)
        self.assert_204(response)

    def test_delete_project_normal(self):
        project = self.create(Project, role=self.admin_role)
        user = self.create(User)

        project.add_member(user)

        url = '/api/v1/projects/{}/'.format(project.id)
        self.authenticate(user)

        response = self.client.delete(url)
        self.assert_403(response)

    def test_get_project_role(self):
        project = self.create(Project, role=self.admin_role)
        user = self.create(User)
        project.add_member(user)

        url = '/api/v1/project-roles/'

        self.authenticate()

        response = self.client.get(url)
        self.assert_200(response)

        data = response.json()
        assert "results" in data
        for x in data["results"]:
            assert "setupPermissions" in x
            assert "assessmentPermissions" in x
            assert "entryPermissions" in x
            assert "leadPermissions" in x
            assert "exportPermissions" in x

    def test_can_modify(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        project.add_member(test_user)
        assert project.can_modify(self.user)
        assert not project.can_modify(test_user)

    def test_auto_accept(self):
        # When a project member is added, if there is a pending
        # request for that user, auto accept that request
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=test_user,
            role=self.admin_role
        )
        project.add_member(test_user, self.normal_role, self.user)

        request = ProjectJoinRequest.objects.get(id=request.id)
        self.assertEqual(request.status, 'accepted')
        self.assertEqual(request.responded_by, self.user)

    def test_status_filter(self):
        project1 = self.create(Project, role=self.admin_role, status='active')
        self.create(Project, role=self.admin_role, status='inactive')
        self.create(Project, role=self.admin_role, status='inactive')

        test_user = self.create(User)
        project1.add_member(test_user, role=self.admin_role)

        url = '/api/v1/projects/?status=inactive'
        self.authenticate(test_user)
        response = self.client.get(url)
        self.assertEqual(response.data['count'], 2)

        # try filtering out the active status
        url = '/api/v1/projects/?status=active'
        self.authenticate(test_user)
        response = self.client.get(url)
        self.assertEqual(response.data['count'], 1)

        # try to update the status of the project
        data = {
            'status': 'active'
        }
        url1 = f'/api/v1/projects/{project1.id}/'
        self.authenticate(test_user)
        response = self.client.patch(url1, data)
        self.assert_200(response)
        self.assertEqual(response.data['status'], project1.status)

    def test_involvment_filter(self):
        project1 = self.create(Project, role=self.admin_role)
        project2 = self.create(Project, role=self.admin_role)
        project3 = self.create(Project, role=self.admin_role)

        test_user = self.create(User)
        project1.add_member(test_user, role=self.normal_role)
        project2.add_member(test_user, role=self.normal_role)

        url = '/api/v1/projects/?involvement=my_projects'

        self.authenticate(test_user)
        response = self.client.get(url)
        self.assert_200(response)

        expected = [
            project1.id,
            project2.id
        ]
        obtained = [r['id'] for r in response.data['results']]

        self.assertEqual(response.data['count'], len(expected))
        self.assertTrue(sorted(expected) == sorted(obtained))

        url = '/api/v1/projects/?involvement=not_my_projects'

        self.authenticate(test_user)
        response = self.client.get(url)
        self.assert_200(response)

        expected = [
            project3.id,
        ]
        obtained = [r['id'] for r in response.data['results']]

        self.assertEqual(response.data['count'], len(expected))
        self.assertTrue(sorted(expected) == sorted(obtained))

    def test_project_role_level(self):
        project = self.create(Project, role=self.smaller_admin_role)
        test_user1 = self.create(User)
        test_user2 = self.create(User)
        m1 = project.add_member(test_user1, role=self.normal_role)
        m2 = project.add_member(test_user2, role=self.admin_role)

        url1 = f'/api/v1/projects/{project.id}/project-memberships/{m1.id}/'
        url2 = f'/api/v1/projects/{project.id}/project-memberships/{m2.id}/'

        # Initial condition: We are Admin
        self.authenticate()

        # Condition 1: We are trying to change a normal
        # user's role to Clairvaoyant One
        data = {
            'role': self.admin_role.id,
        }
        response = self.client.patch(url1, data)
        self.assert_400(response)

        # Condition 2: We are trying to change a normal
        # user's role to Admin
        data = {
            'role': self.smaller_admin_role.id,
        }
        response = self.client.patch(url1, data)
        self.assert_200(response)

        # Condition 3: We are trying to change a CO user
        # when he/she is the only CO user in the project
        data = {
            'role': self.smaller_admin_role.id,
        }
        response = self.client.patch(url2, data)
        self.assert_403(response)

        # Condition 4: We are trying to delete a CO user
        # when he/she is the only CO user in the project
        response = self.client.delete(url2)
        self.assert_403(response)

        # Initial condition: We are a CO user
        self.authenticate(test_user2)

        # Condition 5: We are CO user and are trying to
        # delete ourself when there is no other CO user
        # in the project.
        response = self.client.delete(url2)
        self.assert_403(response)

        # Condition 6: We are CO user and are trying to
        # delete ourself when there is at least one other CO user
        # in the project.
        ProjectMembership.objects.filter(
            project=project,
            member=self.user,
        ).update(role=self.admin_role)

        response = self.client.delete(url2)
        self.assert_204(response)

    def _change_project_privacy_test(self, project, status=403, user=None):
        url = f'/api/v1/projects/{project.id}/'

        changed_privacy = not project.is_private
        put_data = {
            'title': project.title,
            'is_private': changed_privacy,
            'organizations': [],
            # Other fields we don't care
        }
        self.authenticate(user)
        response = self.client.put(url, put_data)
        self.assertEqual(response.status_code, status)

        # Try patching, should give 403 as well
        patch_data = {'is_private': changed_privacy}
        response = self.client.patch(url, patch_data)
        self.assertEqual(response.status_code, status)

    def test_project_stats(self):
        project_user = self.create(User)
        non_project_user = self.create(User)

        af = self.create(AnalysisFramework)
        project = self.create(Project, analysis_framework=af)
        project.add_member(project_user)

        w_data = entry_stats_data.WIDGET_DATA
        a_data = entry_stats_data.ATTRIBUTE_DATA

        lead = self.create(Lead, project=project)
        entry = self.create(
            Entry,
            project=project, analysis_framework=af, lead=lead, entry_type=Entry.EXCERPT,
        )

        # Create widgets, attributes and configs
        invalid_stat_config = {}
        valid_stat_config = {}

        for widget_identifier, data_identifier, config_kwargs in [
            ('widget_1d', 'matrix1dWidget', {}),
            ('widget_2d', 'matrix2dWidget', {}),
            ('geo_widget', 'geoWidget', {}),
            (
                'severity_widget',
                'conditionalWidget',
                {
                    'is_conditional_widget': True,
                    'selectors': ['widgets', 0, 'widget'],
                    'widget_key': 'scalewidget-1',
                    'widget_type': 'scaleWidget',
                },
            ),
            ('reliability_widget', 'scaleWidget', {}),
            ('affected_groups_widget', 'multiselectWidget', {}),
            ('specific_needs_groups_widget', 'multiselectWidget', {}),
        ]:
            widget = self.create(
                Widget, analysis_framework=af,
                properties={'data': w_data[data_identifier]},
            )
            self.create(Attribute, entry=entry, widget=widget, data=a_data[data_identifier])
            valid_stat_config[widget_identifier] = {
                'pk': widget.pk,
                **config_kwargs,
            }
            invalid_stat_config[widget_identifier] = {'pk': 0}

        url = f'/api/v1/projects/{project.pk}/project-viz/'

        # 404 for non project user
        self.authenticate(non_project_user)
        response = self.client.get(url)
        self.assert_404(response)

        self.authenticate(project_user)

        # 404 for project user if config is not set
        response = self.client.get(url)
        self.assert_404(response)

        af.properties = {'stats_config': invalid_stat_config}
        af.save()

        # 202 if config is set
        response = self.client.get(url)
        self.assert_202(response)

        # 500 if invalid config is set and stat is generated
        _generate_project_viz_stats(project.pk)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.json()['status'], 'failure')

        af.properties = {'stats_config': valid_stat_config}
        af.save()

        # 302 (Redirect to data file) if valid config is set and stat is generated
        _generate_project_viz_stats(project.pk)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.json()['status'], 'success')
        return project

    def test_project_lead_groups_api(self):
        project = self.create_project(role=self.normal_role)
        lead_group1 = self.create(LeadGroup, project=project)
        lead_group2 = self.create(LeadGroup, project=project)

        url = f'/api/v1/projects/{project.pk}/lead-groups/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        # Only provide projects leads-group [Pagination is done for larger dataset]
        assert set([lg['id'] for lg in response.json()['results']]) ==\
            set([lead_group1.pk, lead_group2.pk])

    def test_project_memberships_if_not_in_project(self):
        """
        NOTE: This test include the test for ProjectSerializer that doesnot return the memberships
        """
        project = self.create(Project, is_private=False)
        user1 = self.create(User)
        user2 = self.create(User)
        project.add_member(user1, role=self.admin_role)

        url = '/api/v1/projects/'
        self.authenticate(user2)  # authenticate with another user that is not project member
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data['count'], 1)  # there should be one project
        self.assertEqual(response.data['results'][0]['id'], project.id)
        self.assertNotIn('memberships', response.data['results'][0])  # No memberships field should be shown

    def test_project_memberships_in_particluar_project(self):
        project1 = self.create(Project, is_private=False)
        user1 = self.create(User)
        user2 = self.create(User)
        project1.add_member(user1, role=self.admin_role)

        url = f'/api/v1/projects/{project1.id}/'
        self.authenticate(user1)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data['id'], project1.id)
        self.assertIn('memberships', response.data)
        self.assertEqual(response.data['memberships'][0]['member'], user1.id)

        # same project authenticate with not member user
        self.authenticate(user2)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data['id'], project1.id)
        self.assertNotIn('memberships', response.data)  # `membership` field shouldnot be present

    def test_project_summary_api(self):
        user = self.create_user()

        project1 = self.create_project(title='Project 1')
        project2 = self.create_project(title='Project 2')
        project3 = self.create_project(title='Project 3')
        project1.add_member(user)
        project2.add_member(user)
        project3.add_member(user)

        lead1 = self.create_lead(project=project1)
        lead2 = self.create_lead(project=project1)
        lead3 = self.create_lead(project=project2)
        lead4 = self.create_lead(project=project3)
        self.create_lead(project=project1)

        now = timezone.now()
        self.update_obj(self.create_entry(lead=lead1, controlled=True), created_at=now + relativedelta(months=-3, days=-1))
        self.update_obj(self.create_entry(lead=lead1, controlled=True), created_at=now + relativedelta(months=-2))
        self.update_obj(self.create_entry(lead=lead2, controlled=False), created_at=now + relativedelta(months=-3))
        self.update_obj(self.create_entry(lead=lead2, controlled=True), created_at=now + relativedelta(months=-3))
        self.update_obj(self.create_entry(lead=lead2, controlled=True), created_at=now + relativedelta(months=-3))
        self.update_obj(self.create_entry(lead=lead3, controlled=True), created_at=now + relativedelta(days=-10))
        self.update_obj(self.create_entry(lead=lead3, controlled=True), created_at=now + relativedelta(days=-20))
        self.update_obj(self.create_entry(lead=lead3, controlled=True), created_at=now + relativedelta(days=-30))
        self.update_obj(self.create_entry(lead=lead3, controlled=True), created_at=now + relativedelta(days=-40))
        self.update_obj(self.create_entry(lead=lead4, controlled=False), created_at=now + relativedelta(months=-3, days=-1))

        self.authenticate(user)
        url = '/api/v1/projects-stat/summary/'
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data['projects_count'], 3)
        self.assertEqual(response.data['total_leads_count'], 5)
        self.assertEqual(response.data['total_leads_tagged_count'], 4)
        self.assertEqual(response.data['total_leads_tagged_and_controlled_count'], 2)
        self.assertEqual(len(response.data['recent_entries_activity']['projects']), 2)
        self.assertEqual(len(response.data['recent_entries_activity']['activities']), 5)

    def test_project_recent_api(self):
        user = self.create_user()

        project1 = self.create_project(title='Project 1')
        project2 = self.create_project(title='Project 2')
        project3 = self.create_project(title='Project 3')
        project4 = self.create_project(title='Project 4')
        project1.add_member(user)
        project2.add_member(user)
        project3.add_member(user)

        lead1 = self.create_lead(project=project1, created_by=user)
        lead2 = self.create_lead(project=project2, created_by=user)
        self.create_entry(lead=lead1, controlled=False, created_by=user)
        self.create_lead(project=project3, created_by=user)
        self.create_lead(project=project4, created_by=user)

        self.authenticate(user)
        url = '/api/v1/projects-stat/recent/'
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]['id'], project3.pk)
        self.assertEqual(response.data[1]['id'], project1.pk)
        self.assertEqual(response.data[2]['id'], project2.pk)

        lead2.modified_by = user
        lead2.save()
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]['id'], project2.pk)

    def test_project_stats_api(self):
        user = self.create_user()

        project1 = self.create_project(title='Project 1')
        project2 = self.create_project(title='Project 2')
        project3 = self.create_project(title='Project 3')
        project1.add_member(user)
        project2.add_member(user)

        now = timezone.now()
        lead1_1 = self.update_obj(self.create_lead(project=project1), created_at=now + relativedelta(months=-1))
        lead1_2 = self.update_obj(self.create_lead(project=project1), created_at=now + relativedelta(months=-2))
        lead1_3 = self.update_obj(self.create_lead(project=project1), created_at=now + relativedelta(months=-2))
        lead1_4 = self.update_obj(self.create_lead(project=project1), created_at=now + relativedelta(months=-1))
        self.update_obj(self.create_lead(project=project1), created_at=now + relativedelta(months=-1))

        self.update_obj(self.create_entry(lead=lead1_1, controlled=False), created_at=now + relativedelta(months=-1))
        self.update_obj(self.create_entry(lead=lead1_1, controlled=False), created_at=now + relativedelta(months=-1))
        self.update_obj(self.create_entry(lead=lead1_2, controlled=True), created_at=now + relativedelta(months=-3))
        self.update_obj(self.create_entry(lead=lead1_2, controlled=False), created_at=now + relativedelta(months=-2))
        self.update_obj(self.create_entry(lead=lead1_2, controlled=True), created_at=now + relativedelta(months=-2))
        self.update_obj(self.create_entry(lead=lead1_3, controlled=True), created_at=now + relativedelta(months=-3))
        self.update_obj(self.create_entry(lead=lead1_3, controlled=True), created_at=now + relativedelta(months=-3))
        self.create_entry(lead=lead1_3, controlled=True)
        self.create_entry(lead=lead1_4, controlled=True)

        lead2 = self.create_lead(project=project2)
        lead3 = self.create_lead(project=project3)
        self.create_entry(lead=lead2, controlled=False)
        self.create_entry(lead=lead3, controlled=False)

        # Run the caching process
        _generate_project_stats_cache()

        self.authenticate(user)
        url = '/api/v1/projects-stat/?involvement=my_projects'
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data['results']), 2)
        # Check response for Project 1
        project_1_data = next(
            project for project in response.data['results'] if project['id'] == project1.pk
        )
        self.assertEqual(project_1_data['id'], project1.pk)
        self.assertEqual(project_1_data['number_of_leads'], 5)
        self.assertEqual(project_1_data['number_of_leads_tagged'], 4)
        self.assertEqual(project_1_data['number_of_leads_tagged_and_controlled'], 2)
        self.assertEqual(project_1_data['number_of_entries'], 9)
        self.assertEqual(len(project_1_data['leads_activity']), 2)
        self.assertEqual(len(project_1_data['entries_activity']), 3)

    def test_project_stats_public_api(self):
        normal_user = self.create_user()
        admin_user = self.create_user()
        member_user = self.create_user()

        project = self.test_project_stats()
        project.add_member(admin_user, role=self.admin_role)
        project.add_member(member_user, role=self.normal_role)

        url = f'/api/v1/projects/{project.pk}/public-viz/'

        # Check permission for token generation
        for action in ['new', 'off', 'new', 'on', 'random']:
            for user, assertLogic in [
                (normal_user, self.assert_403),
                (member_user, self.assert_403),
                (admin_user, self.assert_200),
            ]:
                self.authenticate(user)
                current_stats = ProjectStats.objects.get(project=project)
                response = self.client.post(url, data={'action': action})
                if action == 'random' and assertLogic == self.assert_200:
                    self.assert_400(response)
                else:
                    assertLogic(response)
                if assertLogic == self.assert_200:
                    if action == 'new':
                        assert response.data['public_url'] != current_stats.token
                        # Logout and check if response is okay
                        self.client.logout()
                        response = self.client.get(f"{response.data['public_url']}?format=json")
                        self.assert_200(response)
                    elif action == 'on':
                        assert (
                            response.data['public_url'] is not None
                        ) or (
                            response.data['public_url'] == current_stats.token
                        )
                        # Logout and check if response is not okay
                        self.client.logout()
                        response = self.client.get(f"{response.data['public_url']}?format=json")
                        self.assert_200(response)
                    elif action == 'off':
                        assert (
                            response.data['public_url'] is not None
                        ) or (
                            response.data['public_url'] == current_stats.token
                        )
                        # Logout and check if response is not okay
                        self.client.logout()
                        response = self.client.get(f"{response.data['public_url']}?format=json")
                        self.assert_403(response)

        # Make sure response are only for valid token
        self.client.logout()
        stats = ProjectStats.objects.get(project=project)
        stats.token = uuid.uuid4()
        stats.public_share = True
        stats.save()
        viz_public_url = stats.get_public_url()
        response = self.client.get(f"{viz_public_url}?format=json")
        self.assert_200(response)
        # Disabling public_share
        stats.public_share = False
        stats.save()
        response = self.client.get(f"{viz_public_url}?format=json")
        self.assert_403(response)
        # Removing token
        stats.token = None
        stats.public_share = True
        stats.save()
        response = self.client.get(f"{viz_public_url}?format=json")
        self.assert_403(response)

    def test_project_recent_activities_api(self):
        normal_user = self.create_user()
        member_user = self.create_user()

        project = self.create_project(title='Project 1')
        project.add_member(member_user)

        now = timezone.now()
        # Leads
        lead1 = self.update_obj(self.create_lead(project=project), created_at=now + relativedelta(months=-1))
        lead2 = self.update_obj(self.create_lead(project=project), created_at=now + relativedelta(months=-2))
        lead3 = self.update_obj(self.create_lead(project=project), created_at=now + relativedelta(months=-2))

        # Entries
        self.update_obj(self.create_entry(lead=lead1, project=project), created_at=now + relativedelta(months=-1))
        self.update_obj(self.create_entry(lead=lead1, project=project), created_at=now + relativedelta(months=-1))
        self.update_obj(self.create_entry(lead=lead2, project=project), created_at=now + relativedelta(months=-3))
        self.update_obj(self.create_entry(lead=lead2, project=project), created_at=now + relativedelta(months=-2))
        self.update_obj(self.create_entry(lead=lead2, project=project), created_at=now + relativedelta(months=-2))
        self.update_obj(self.create_entry(lead=lead3, project=project), created_at=now + relativedelta(months=-3))
        entry = self.update_obj(self.create_entry(lead=lead3, project=project), created_at=now + relativedelta(months=-3))

        # Entries Comments
        entry_comment = self.create(EntryComment, entry=entry)
        self.create(EntryCommentText, comment=entry_comment, text='Old')
        self.create(EntryCommentText, comment=entry_comment, text='New')

        url = '/api/v1/projects/recent-activities/'

        self.authenticate(normal_user)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data['results']), 0)

        self.authenticate(member_user)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data['results']), 11)
