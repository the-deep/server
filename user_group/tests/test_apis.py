from deep.tests import TestCase
from user.models import User
from user_group.models import UserGroup, GroupMembership


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
        user_group = self.create(UserGroup)
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

    def test_add_member(self):
        user_group = self.create(UserGroup)
        test_user = self.create(User)

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
