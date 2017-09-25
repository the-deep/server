from rest_framework import status
from rest_framework.test import APITestCase
from user.tests.test_apis import AuthMixin
from user_group.models import UserGroup, GroupMembership


class UserGroupMixin():
    """
    User Group related methods
    """
    def create_or_get_user_group(self):
        """
        Create new or return recent user group
        """
        user_group = UserGroup.objects.first()
        if not user_group:
            user_group = UserGroup.objects.create(
                title='Test user group',
            )

            if self.user:
                GroupMembership.objects.create(
                    member=self.user,
                    group=user_group,
                    role='admin',
                )

        return user_group


class UserGroupApiTest(AuthMixin, UserGroupMixin, APITestCase):
    """
    User Group Tests
    """
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

    def test_create_user_group(self):
        """
        Create User Group Test
        """
        url = '/api/v1/user-groups/'
        data = {
            'title': 'Test user group',
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserGroup.objects.count(), 1)
        self.assertEqual(response.data['title'], data['title'])

        # Test that the user has been made admin
        self.assertEqual(len(response.data['members']), 1)
        self.assertEqual(response.data['members'][0], self.user.pk)

        self.assertEqual(len(response.data['memberships']), 1)

        membership = GroupMembership.objects.get(
            pk=response.data['memberships'][0])
        self.assertEqual(membership.member.pk, self.user.pk)
        self.assertEqual(membership.role, 'admin')

    def test_add_member(self):
        """
        Add UserGroup Members
        """
        user_group = self.create_or_get_user_group()

        test_user = self.create_new_user()

        url = '/api/v1/group-memberships/'
        data = {
            'member': test_user.pk,
            'group': user_group.pk,
            'role': 'normal',
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], data['role'])
        self.assertEqual(response.data['member'], data['member'])
        self.assertEqual(response.data['group'], data['group'])


# EOF
