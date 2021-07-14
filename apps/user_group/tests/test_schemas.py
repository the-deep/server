from utils.graphene.tests import GraphqlTestCase

from user.factories import UserFactory
from user_group.factories import UserGroupFactory
from user_group.models import UserGroup


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
                  globalCrisisMonitoring
                  description
                  customProjectFields
                  createdAt
                  clientId
                  currentUserRole
                  memberships {
                    role
                    member {
                      id
                      displayName
                    }
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
        ug_with_admin_membership = UserGroupFactory.create()
        ug_with_admin_membership.add_member(user, role='admin')
        ug_without_membership = UserGroupFactory.create(members=[another_user])

        results = self.query_check(query)['data']['userGroups']['results']
        self.assertEqual(len(results), 3, results)
        for index, (user_group, memberships_count, current_user_role) in enumerate([
            # as normal member
            (ug_with_membership, 2, 'normal'),
            # as admin member
            (ug_with_admin_membership, 1, 'admin'),
            # as non member
            (ug_without_membership, 0, None),
        ]):
            self.assertEqual(results[index]['id'], str(user_group.pk), results[index])
            self.assertEqual(len(results[index]['memberships']), memberships_count, results[index])
            self.assertEqual(results[index]['currentUserRole'], current_user_role, results[index])

    def test_user_group_query(self):
        # Try with random user
        query = '''
            query Query($id: ID!) {
              userGroup(id: $id) {
                id
                title
                modifiedAt
                globalCrisisMonitoring
                description
                customProjectFields
                createdAt
                clientId
                currentUserRole
                memberships {
                  role
                  member {
                    id
                    displayName
                  }
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
        self.assertEqual(len(content['data']['userGroup']['memberships']), 0, content)

        # -- Create new user groups w/wo user as member
        # with login, non-member usergroup will give real members
        ug_with_membership = UserGroupFactory.create(members=[user, another_user])
        content = self.query_check(query, variables={'id': str(ug_with_membership.pk)})
        self.assertEqual(len(content['data']['userGroup']['memberships']), 2, content)
        self.assertEqual(content['data']['userGroup']['currentUserRole'], 'normal', content)

    def test_user_group_create_mutation(self):
        query = '''
            mutation MyMutation($input: UserGroupInputType!) {
              createUserGroup(data: $input) {
                ok
                errors
                result {
                  id
                  title
                  modifiedAt
                  modifiedBy {
                    id
                    displayName
                  }
                  createdBy {
                    id
                    displayName
                  }
                  createdAt
                  memberships {
                    member {
                      id
                      displayName
                    }
                    role
                    addedBy {
                      id
                      displayName
                    }
                  }
                }
              }
            }
        '''
        user = UserFactory.create()
        another_user = UserFactory.create()
        minput = dict(
            title='New user group from mutation',
            memberships=[dict(
                member=str(another_user.pk),
                role='normal',
            )],
        )
        self.query_check(query, minput=minput, assert_for_error=True)

        self.force_login(user)
        # TODO: Add permission check
        # content = self.query_check(query, minput=minput, okay=False)
        # Response with new user group
        result = self.query_check(query, minput=minput, okay=True)['data']['createUserGroup']['result']
        self.assertEqual(result['title'], minput['title'], result)
        self.assertEqual(len(result['memberships']), 2, result)
        # Another user as normal member
        self.assertEqual(result['memberships'][0]['member']['id'], minput['memberships'][0]['member'], result)
        self.assertEqual(result['memberships'][0]['role'], minput['memberships'][0]['role'].upper(), result)  # noqa:E501 FIXME: why upper()
        self.assertEqual(result['memberships'][0]['addedBy']['id'], str(user.pk), result)  # Current user
        # Current user as admin
        self.assertEqual(result['memberships'][1]['member']['id'], str(user.pk), result)
        self.assertEqual(result['memberships'][1]['role'], 'admin'.upper(), result)  # FIXME: why upper()
        self.assertEqual(result['memberships'][1]['addedBy'], None, result)  # Automate

    def test_user_group_update_mutation(self):
        query = '''
            mutation MyMutation($input: UserGroupInputType! $id: ID!) {
              updateUserGroup(data: $input id: $id) {
                ok
                errors
                result {
                  id
                  title
                  modifiedAt
                  modifiedBy {
                    id
                    displayName
                  }
                  createdBy {
                    id
                    displayName
                  }
                  createdAt
                  memberships {
                    member {
                      id
                      displayName
                    }
                    role
                    addedBy {
                      id
                      displayName
                    }
                  }
                }
              }
            }
        '''
        user = UserFactory.create()
        another_user = UserFactory.create()
        new_another_user = UserFactory.create()
        ug = UserGroupFactory.create(title='User-Group 101', members=[another_user], created_by=user)
        ug.add_member(user, role='admin')
        minput = dict(
            title='User-Group 101 (Updated)',
        )
        self.query_check(query, minput=minput, assert_for_error=True, variables={'id': str(ug.pk)})

        self.force_login(user)
        # TODO: Add permission check
        # content = self.query_check(query, minput=minput, okay=False, variables={'id': str(ug.pk)})
        # Response with new user group
        result = self.query_check(
            query, minput=minput, okay=True, variables={'id': str(ug.pk)}
        )['data']['updateUserGroup']['result']

        self.assertEqual(result['title'], minput['title'], result)
        self.assertEqual(len(result['memberships']), 2, result)

        minput.update(dict(
            memberships=[
                dict(member=str(new_another_user.pk), role='admin'),
            ]
        ))
        result = self.query_check(
            query, minput=minput, okay=True,
            variables={'id': str(ug.pk)}
        )['data']['updateUserGroup']['result']
        self.assertEqual(len(result['memberships']), 2, result)
        # New another user added as normal member (and another_user no longer exists in the group)
        self.assertEqual(result['memberships'][0]['member']['id'], minput['memberships'][0]['member'], result)
        self.assertEqual(result['memberships'][0]['role'], minput['memberships'][0]['role'].upper(), result)  # noqa:E501 FIXME: why upper()
        self.assertEqual(result['memberships'][0]['addedBy']['id'], str(user.pk), result)  # Current user
        # Make sure admin (created_by) user is not removed even if not provided while updating
        self.assertEqual(result['memberships'][1]['member']['id'], str(user.pk), result)
        self.assertEqual(result['memberships'][1]['role'], 'admin'.upper(), result)  # FIXME: why upper()
        self.assertEqual(result['memberships'][1]['addedBy'], None, result)  # Automate

    def test_user_group_delete_mutation(self):
        query = '''
            mutation MyMutation($id: ID!) {
              deleteUserGroup(id: $id) {
                ok
                errors
                result {
                  id
                  title
                }
              }
            }
        '''
        user = UserFactory.create()
        ug = UserGroupFactory.create(title='User-Group 101')
        ug.add_member(user, role='admin')
        self.query_check(query, assert_for_error=True, variables={'id': str(ug.pk)})

        self.force_login(user)
        # TODO: Add permission check
        # content = self.query_check(query, okay=False, variables={'id': str(ug.pk)})
        # Response with new user group
        result = self.query_check(query, okay=True, variables={'id': str(ug.pk)})['data']['deleteUserGroup']['result']

        # New another user added as normal member (and another_user no longer exists in the group)
        self.assertEqual(result['id'], str(ug.id), result)
        self.assertEqual(result['title'], ug.title, result)
        with self.assertRaises(UserGroup.DoesNotExist):  # Make sure user_group doesn't exists anymore
            ug.refresh_from_db()
