from utils.graphene.tests import GraphqlTestCase

from user.factories import UserFactory
from user_group.factories import UserGroupFactory


class TestUserGroupSchema(GraphqlTestCase):
    def test_user_groups_query(self):
        # Try with random user
        query = '''
            query Query {
              userGroups(ordering: "id") {
                results {
                  id
                  title
                  modifiedAt
                  isCurrentUserMember
                  globalCrisisMonitoring
                  description
                  customProjectFields
                  createdAt
                  clientId
                  members {
                    id
                    displayName
                  }
                  createdBy {
                    id
                    displayName
                  }
                  modifiedBy {
                    id
                    displayName
                  }
                }
              }
            }
        '''
        # Without login, throw error
        self.query_check(query, assert_for_error=True)

        # -- Create new user and login --
        user = UserFactory.create()
        another_user = UserFactory.create()
        self.force_login(user)

        # with login, return empty list
        content = self.query_check(query)
        self.assertEqual(len(content['data']['userGroups']['results']), 0, content)

        # -- Create new user groups w/wo user as member
        # Try with real user
        ug_with_membership = UserGroupFactory.create(members=[user, another_user])
        ug_without_membership = UserGroupFactory.create(members=[another_user])

        results = self.query_check(query)['data']['userGroups']['results']
        self.assertEqual(len(results), 2, content)
        self.assertEqual(results[0]['id'], str(ug_with_membership.pk), content)
        self.assertEqual(len(results[0]['members']), 2, content)
        self.assertEqual(results[1]['id'], str(ug_without_membership.pk), content)
        # Only member can see other members
        self.assertEqual(len(results[1]['members']), 0, content)

    def test_user_group_query(self):
        # Try with random user
        query = '''
            query Query($id: ID!) {
              userGroup(id: $id) {
                id
                title
                modifiedAt
                isCurrentUserMember
                globalCrisisMonitoring
                description
                customProjectFields
                createdAt
                clientId
                members {
                  id
                  displayName
                }
                createdBy {
                  id
                  displayName
                }
                modifiedBy {
                  id
                  displayName
                }
              }
            }
        '''
        another_user = UserFactory.create()
        ug_without_membership = UserGroupFactory.create(members=[another_user])

        # Without login, throw error
        self.query_check(query, assert_for_error=True, variables={'id': str(ug_without_membership.pk)})

        # -- Create new user and login --
        user = UserFactory.create()
        self.force_login(user)

        # with login, non-member usergroup will give zero members
        content = self.query_check(query, variables={'id': str(ug_without_membership.pk)})
        self.assertEqual(len(content['data']['userGroup']['members']), 0, content)

        # -- Create new user groups w/wo user as member
        # with login, non-member usergroup will give real members
        ug_with_membership = UserGroupFactory.create(members=[user, another_user])
        content = self.query_check(query, variables={'id': str(ug_with_membership.pk)})
        self.assertEqual(len(content['data']['userGroup']['members']), 2, content)

    def test_user_group_mutation(self):
        pass
