from deep.tests import TestCase
from user.models import User
from user_group.models import UserGroup, GroupMembership
from project.models import (
    Project,
    ProjectMembership,
    ProjectUserGroupMembership
)


class UserGroupApiTest(TestCase):
    def test_create_user_group(self):
        user_group_count = UserGroup.objects.count()

        url = '/api/v1/user-groups/'
        data = {
            'title': 'Test user group',
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(UserGroup.objects.count(), user_group_count + 1)
        self.assertEqual(response.data['title'], data['title'])

        # Test that the user has been made admin
        self.assertEqual(len(response.data['memberships']), 1)
        self.assertEqual(response.data['memberships'][0]['member'],
                         self.user.pk)

        membership = GroupMembership.objects.get(
            pk=response.data['memberships'][0]['id'])
        self.assertEqual(membership.member.pk, self.user.pk)
        self.assertEqual(membership.role, 'admin')

    def test_member_of(self):
        user_group = self.create(UserGroup, role='admin')
        test_user = self.create(User)

        url = '/api/v1/user-groups/member-of/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], user_group.id)

        url = '/api/v1/user-groups/member-of/?user={}'.format(test_user.id)

        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 0)

    def test_search_user_usergroups_validation_empty_query(self):
        url = '/api/v1/users-user-groups/?search='
        self.authenticate()
        response = self.client.get(url)
        self.assert_400(response)

    def test_search_user_usergroups(self):
        user_group = self.create(UserGroup, title="MyTestUserGroup")
        test_user = self.create(User, username="mytestuser")
        # Query should be mytest to match just
        # the above created usergroup and user
        url = '/api/v1/users-user-groups/?search=mytest'

        # should return both user and usergroup
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        data = response.json()

        assert 'results' in data
        self.assertEqual(len(data['results']), 2)

        for item in data['results']:
            assert 'id' in item
            assert 'type' in item
            assert item['type'] in ['user', 'user_group']

        users = [x for x in data['results'] if x['type'] == 'user']
        user_groups = [x for x in data['results'] if x['type'] == 'user_group']

        self.assertEqual(users[0]['id'], test_user.id)
        self.assertEqual(user_groups[0]['id'], user_group.id)

    def test_add_member(self):
        # check if project membership changes or not
        project = self.create(
            Project,
            user_groups=[],
            title='TestProject',
            role=self.admin_role
        )
        user_group = self.create(UserGroup, role='admin')
        test_user = self.create(User)

        ProjectUserGroupMembership.objects.create(
            usergroup=user_group,
            project=project
        )
        memberships = ProjectMembership.objects.filter(project=project)
        initial_member_count = memberships.count()

        url = '/api/v1/group-memberships/'
        data = {
            'member': test_user.pk,
            'group': user_group.pk,
            'role': 'normal',
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(response.data['role'], data['role'])
        self.assertEqual(response.data['member'], data['member'])
        self.assertEqual(response.data['group'], data['group'])

        # check for project memberships
        final_memberships = ProjectMembership.objects.filter(project=project)
        final_membership_count = final_memberships.count()
        self.assertEqual(initial_member_count + 1, final_membership_count)

    def test_delete_user_group(self):
        # first create a user group
        project = self.create(Project, role=self.admin_role)
        # set directly_added as True
        memship = ProjectMembership.objects.filter(project=project).last()
        memship.is_directly_added = True
        memship.save()

        mems_count = ProjectMembership.objects.filter(project=project).count()
        self.assertEqual(mems_count, 1)

        # create user group
        user_group = self.create(UserGroup, role='admin')

        # add usergroup to project
        ProjectUserGroupMembership.objects.create(
            usergroup=user_group,
            project=project
        )

        test_user = self.create(User)
        gm = GroupMembership.objects.create(member=test_user, group=user_group)

        mems_count = ProjectMembership.objects.filter(project=project).count()
        self.assertEqual(mems_count, 2)  # we added a user

        # now delete
        url = '/api/v1/group-memberships/{}/'.format(gm.id)
        self.authenticate()

        response = self.client.delete(url)
        assert response.status_code == 204

        # check for project memberships
        final_memberships = ProjectMembership.objects.filter(project=project)
        final_membership_count = final_memberships.count()
        self.assertEqual(final_membership_count, 1)
