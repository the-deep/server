from utils.graphene.tests import GraphQLTestCase

from user.factories import UserFactory
from user_group.factories import UserGroupFactory
from user_group.models import UserGroup, GroupMembership


class TestUserGroupSchema(GraphQLTestCase):
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
                  membershipsCount
                  memberships {
                    role
                    member {
                      id
                      profile {
                          displayName
                      }
                    }
                  }
                  createdBy {
                    id
                    profile {
                        displayName
                    }
                  }
                  modifiedBy {
                    id
                    profile {
                        displayName
                    }
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
        ug_with_admin_membership.add_member(user, role=GroupMembership.Role.ADMIN)
        ug_without_membership = UserGroupFactory.create(members=[another_user])

        results = self.query_check(query)['data']['userGroups']['results']
        self.assertEqual(len(results), 3, results)
        for index, (user_group, memberships_count, real_memberships_count, current_user_role) in enumerate([
            # as normal member
            (ug_with_membership, 2, 2, self.genum(GroupMembership.Role.NORMAL)),
            # as admin member
            (ug_with_admin_membership, 1, 1, self.genum(GroupMembership.Role.ADMIN)),
            # as non member
            (ug_without_membership, 0, 1, None),
        ]):
            self.assertEqual(results[index]['id'], str(user_group.pk), results[index])
            self.assertEqual(len(results[index]['memberships']), memberships_count, results[index])
            self.assertEqual(results[index]['membershipsCount'], real_memberships_count, results[index])
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
                membershipsCount
                memberships {
                  role
                  member {
                    id
                    profile {
                        displayName
                    }
                  }
                }
                createdBy {
                  id
                  profile {
                      displayName
                  }
                }
                modifiedBy {
                  id
                  profile {
                      displayName
                  }
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

        # with login, non-member usergroup will give zero members but membershipsCount 1
        content = self.query_check(query, variables={'id': str(ug_without_membership.pk)})
        self.assertEqual(content['data']['userGroup']['membershipsCount'], 1, content)
        self.assertEqual(len(content['data']['userGroup']['memberships']), 0, content)

        # -- Create new user groups w/wo user as member
        # with login, non-member usergroup will give real members
        ug_with_membership = UserGroupFactory.create(members=[user, another_user])
        content = self.query_check(query, variables={'id': str(ug_with_membership.pk)})
        self.assertEqual(content['data']['userGroup']['membershipsCount'], 2, content)
        self.assertEqual(len(content['data']['userGroup']['memberships']), 2, content)
        self.assertEqual(content['data']['userGroup']['currentUserRole'], self.genum(GroupMembership.Role.NORMAL), content)

    def test_user_group_create_mutation(self):
        query = '''
            mutation MyMutation($input: UserGroupInputType!) {
              userGroupCreate(data: $input) {
                ok
                errors
                result {
                  id
                  title
                  modifiedAt
                  modifiedBy {
                    id
                    profile {
                        displayName
                    }
                  }
                  createdBy {
                    id
                    profile {
                        displayName
                    }
                  }
                  createdAt
                  membershipsCount
                  memberships {
                    member {
                      id
                      profile {
                          displayName
                      }
                    }
                    role
                    addedBy {
                      id
                      profile {
                          displayName
                      }
                    }
                  }
                }
              }
            }
        '''
        user = UserFactory.create()
        minput = dict(title='New user group from mutation')
        self.query_check(query, minput=minput, assert_for_error=True)

        self.force_login(user)
        # TODO: Add permission check
        # content = self.query_check(query, minput=minput, okay=False)
        # Response with new user group
        result = self.query_check(query, minput=minput, okay=True)['data']['userGroupCreate']['result']
        self.assertEqual(result['title'], minput['title'], result)
        self.assertEqual(result['membershipsCount'], 1, result)

    def test_user_group_update_mutation(self):
        query = '''
            mutation MyMutation($input: UserGroupInputType! $id: ID!) {
              userGroup(id: $id) {
                  userGroupUpdate(data: $input) {
                    ok
                    errors
                    result {
                      id
                      title
                      modifiedAt
                      modifiedBy {
                        id
                        profile {
                            displayName
                        }
                      }
                      createdBy {
                        id
                        profile {
                            displayName
                        }
                      }
                      createdAt
                      membershipsCount
                      memberships {
                        member {
                          id
                          profile {
                              displayName
                          }
                        }
                        role
                        addedBy {
                          id
                          profile {
                              displayName
                          }
                        }
                      }
                    }
                  }
              }
            }
        '''
        user = UserFactory.create()
        member_user = UserFactory.create()
        guest_user = UserFactory.create()
        ug = UserGroupFactory.create(title='User-Group 101', members=[member_user], created_by=user)
        ug.add_member(user, role=GroupMembership.Role.ADMIN)
        minput = dict(
            title='User-Group 101 (Updated)',
        )
        self.query_check(query, minput=minput, assert_for_error=True, variables={'id': str(ug.pk)})

        for _user in [guest_user, member_user]:
            self.force_login(_user)
            self.query_check(
                query, minput=minput, assert_for_error=True, variables={'id': str(ug.pk)}
            )

        self.force_login(user)
        result = self.query_check(
            query, minput=minput, okay=True, mnested=['userGroup'], variables={'id': str(ug.pk)}
        )['data']['userGroup']['userGroupUpdate']['result']

        self.assertEqual(result['title'], minput['title'], result)
        self.assertEqual(result['membershipsCount'], 2, result)
        self.assertEqual(len(result['memberships']), 2, result)

        result = self.query_check(
            query,
            minput=minput,
            okay=True,
            mnested=['userGroup'],
            variables={'id': str(ug.pk)}
        )['data']['userGroup']['userGroupUpdate']['result']
        self.assertEqual(result['membershipsCount'], 2, result)
        self.assertEqual(len(result['memberships']), 2, result)
        self.assertEqual(result['memberships'][1]['member']['id'], str(user.pk), result)
        self.assertEqual(result['memberships'][1]['role'], self.genum(GroupMembership.Role.ADMIN), result)

    def test_user_group_delete_mutation(self):
        query = '''
            mutation MyMutation($id: ID!) {
              userGroup(id: $id) {
                  userGroupDelete {
                    ok
                    errors
                    result {
                      id
                      title
                    }
                  }
              }
            }
        '''
        user = UserFactory.create()
        guest_user = UserFactory.create()
        member_user = UserFactory.create()
        ug = UserGroupFactory.create(title='User-Group 101', created_by=user)
        ug.add_member(user, role=GroupMembership.Role.ADMIN)
        ug.add_member(member_user, role=GroupMembership.Role.ADMIN)
        self.query_check(query, assert_for_error=True, variables={'id': str(ug.pk)})

        for _user in [guest_user, member_user]:
            self.force_login(_user)
            self.query_check(query, assert_for_error=True, variables={'id': str(ug.pk)})

        self.force_login(user)
        result = self.query_check(
            query,
            okay=True,
            mnested=['userGroup'],
            variables={'id': str(ug.pk)},
        )['data']['userGroup']['userGroupDelete']['result']

        self.assertEqual(result['id'], str(ug.id), result)
        self.assertEqual(result['title'], ug.title, result)
        with self.assertRaises(UserGroup.DoesNotExist):  # Make sure user_group doesn't exists anymore
            ug.refresh_from_db()
