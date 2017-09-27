from rest_framework import status
from rest_framework.test import APITestCase
from user.tests.test_apis import AuthMixin
from user_group.tests.test_apis import UserGroupMixin
from user_group.models import GroupMembership


class UserGroupPermissionsTest(AuthMixin, UserGroupMixin, APITestCase):
    """
    Permission tests for user group api

    Only failed permission tests are performed here
    as the successful ones are auto tested in the proper
    apis tests.
    """
    def setUp(self):
        self.auth = self.get_auth()

        # Create a user group and a new test user
        user_group = self.create_or_get_user_group()
        test_user = self.create_new_user()

        # Change admin to new test user
        GroupMembership.objects.filter(
            group=user_group
        ).delete()

        GroupMembership.objects.create(
            group=user_group,
            member=test_user,
            role='admin',
        )

        # The url and data used for requests
        self.url = '/api/v1/user-groups/{}/'.format(user_group.id)
        self.data = {
            'title': 'Changed title',
        }
        self.user_group = user_group

    def get_patch_response(self):
        # Try a patch request
        response = self.client.patch(self.url, self.data,
                                     HTTP_AUTHORIZATION=self.auth,
                                     format='json')
        return response

    def test_404(self):
        """
        Test whether a non-member can see the user_group
        """

        # We should get 404 error since the user is not a member
        # of the user group and cannot see the resource
        self.assertEqual(self.get_patch_response().status_code,
                         status.HTTP_404_NOT_FOUND)

    def test_403(self):
        """
        Test whether a non-admin member can modify the user group
        """
        # Now make the user member, but not admin
        # and test again

        GroupMembership.objects.create(
            group=self.user_group,
            member=self.user,
            role='normal',
        )

        # We should get 403 error
        self.assertEqual(self.get_patch_response().status_code,
                         status.HTTP_403_FORBIDDEN)
