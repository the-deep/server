from utils.graphene.tests import GraphQLSnapShotTestCase

from user_group.models import GroupMembership

from user.factories import UserFactory
from user_group.factories import UserGroupFactory


class TestUserGroupMutationSnapShotTestCase(GraphQLSnapShotTestCase):
    factories_used = [UserGroupFactory]

    def test_usergroup_membership_bulk(self):
        query = '''
          mutation MyMutation(
              $id: ID!,
              $ugMembership: [BulkUserGroupMembershipInputType!]!,
              $ugMembershipDelete: [ID!]!
          ) {
          __typename
          userGroup(id: $id) {
            id
            title
            userGroupMembershipBulk(items: $ugMembership, deleteIds: $ugMembershipDelete) {
              errors
              result {
                id
                clientId
                joinedAt
                addedBy {
                  id
                  profile {
                      displayName
                  }
                }
                role
                member {
                  id
                  profile {
                      displayName
                  }
                }
              }
              deletedResult {
                id
                clientId
                joinedAt
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
        creater_user = UserFactory.create()
        user = UserFactory.create()
        low_permission_user = UserFactory.create()
        non_member_user = UserFactory.create()

        member_user1 = UserFactory.create()
        member_user2 = UserFactory.create()
        member_user3 = UserFactory.create()
        member_user4 = UserFactory.create()
        member_user5 = UserFactory.create()
        ug = UserGroupFactory.create(created_by=creater_user)
        membership1, _ = ug.add_member(member_user1)
        membership2, _ = ug.add_member(member_user2)
        ug.add_member(member_user5)
        creater_user_membership, _ = ug.add_member(creater_user, role=GroupMembership.Role.ADMIN)
        user_membership, _ = ug.add_member(user, role=GroupMembership.Role.ADMIN)
        ug.add_member(low_permission_user)

        minput = dict(
            ugMembershipDelete=[
                str(membership1.pk),  # This will be only on try 1
                # This shouldn't be on any response (requester + creater)
                str(user_membership.pk),
                str(creater_user_membership.pk),
            ],
            ugMembership=[
                # Try updating membership (Valid)
                dict(
                    member=member_user2.pk,
                    clientId="member-user-2",
                    role=self.genum(GroupMembership.Role.ADMIN),
                    id=membership2.pk,
                ),
                # Try adding already existing member
                dict(
                    member=member_user5.pk,
                    clientId="member-user-5",
                    role=self.genum(GroupMembership.Role.NORMAL),
                ),
                # Try adding new member (Valid on try 1, invalid on try 2)
                dict(
                    member=member_user3.pk,
                    clientId="member-user-3",
                    role=self.genum(GroupMembership.Role.NORMAL),
                ),
                # Try adding new member (without giving role) -> this should use NORMAL role
                # Valid on try 1, invalid on try 2
                dict(
                    member=member_user4.pk,
                    clientId="member-user-4",
                ),
            ],
        )

        def _query_check(**kwargs):
            return self.query_check(
                query,
                mnested=['userGroup'],
                variables={'id': ug.id, **minput},
                **kwargs,
            )
        # ---------- Without login
        _query_check(assert_for_error=True)
        # ---------- With login (with non-member)
        self.force_login(non_member_user)
        _query_check(assert_for_error=True)
        # ---------- With login (with low-permission member)
        self.force_login(non_member_user)
        _query_check(assert_for_error=True)
        # ---------- With login (with higher permission)
        self.force_login(user)
        # ----------------- Some Invalid input
        response = _query_check()['data']['userGroup']['userGroupMembershipBulk']
        self.assertMatchSnapshot(response, 'try 1')
        # ----------------- All valid input
        minput['ugMembership'].pop(1)
        response = _query_check()['data']['userGroup']['userGroupMembershipBulk']
        self.assertMatchSnapshot(response, 'try 2')
