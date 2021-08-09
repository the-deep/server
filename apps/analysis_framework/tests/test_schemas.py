from unittest import mock

import factory

from utils.graphene.tests import GraphQLTestCase, GraphQLSnapShotTestCase

from analysis_framework.models import Widget

from user.factories import UserFactory
from project.factories import ProjectFactory
from organization.factories import OrganizationFactory
from analysis_framework.factories import (
    AnalysisFrameworkFactory,
    SectionFactory,
    WidgetFactory,
)


class TestAnalysisFrameworkQuery(GraphQLSnapShotTestCase):
    def test_analysis_framework_list(self):
        query = '''
            query MyQuery {
              analysisFrameworks (ordering: "id") {
                page
                pageSize
                totalCount
                results {
                  id
                  title
                  description
                  isPrivate
                }
              }
            }
        '''

        user = UserFactory.create()
        private_af = AnalysisFrameworkFactory.create(is_private=True)
        normal_af = AnalysisFrameworkFactory.create()
        member_af = AnalysisFrameworkFactory.create()
        member_af.add_member(user)

        # Without login
        self.query_check(query, assert_for_error=True)

        # With login
        self.force_login(user)

        content = self.query_check(query)
        results = content['data']['analysisFrameworks']['results']
        self.assertEqual(content['data']['analysisFrameworks']['totalCount'], 2)
        self.assertIdEqual(results[0]['id'], normal_af.id)
        self.assertIdEqual(results[1]['id'], member_af.id)
        self.assertNotIn(str(private_af.id), [d['id'] for d in results])  # Can't see private project.

        project = ProjectFactory.create(analysis_framework=private_af)
        # It shouldn't list private AF after adding to a project.
        content = self.query_check(query)
        results = content['data']['analysisFrameworks']['results']
        self.assertEqual(content['data']['analysisFrameworks']['totalCount'], 2)
        self.assertNotIn(str(private_af.id), [d['id'] for d in results])  # Can't see private project.

        project.add_member(user)
        # It should list private AF after user is member of the project.
        content = self.query_check(query)
        results = content['data']['analysisFrameworks']['results']
        self.assertEqual(content['data']['analysisFrameworks']['totalCount'], 3)
        self.assertIn(str(private_af.id), [d['id'] for d in results])  # Can see private project now.

    def test_analysis_framework(self):
        query = '''
            query MyQuery ($id: ID!) {
              analysisFramework(id: $id) {
                id
                currentUserRole
                description
                isPrivate
                title
              }
            }
        '''

        user = UserFactory.create()
        private_af = AnalysisFrameworkFactory.create(is_private=True)
        normal_af = AnalysisFrameworkFactory.create()
        member_af = AnalysisFrameworkFactory.create()
        member_af.add_member(user)

        # Without login
        self.query_check(query, assert_for_error=True, variables={'id': normal_af.pk})

        # With login
        self.force_login(user)

        # Should work for normal AF
        response = self.query_check(query, variables={'id': normal_af.pk})['data']['analysisFramework']
        self.assertIdEqual(response['id'], normal_af.id, response)
        self.assertEqual(response['isPrivate'], False, response)
        # Should work for member AF
        response = self.query_check(query, variables={'id': member_af.pk})['data']['analysisFramework']
        self.assertIdEqual(response['id'], member_af.id, response)
        self.assertEqual(response['isPrivate'], False, response)
        # Shouldn't work for non-member private AF
        response = self.query_check(query, variables={'id': private_af.pk})['data']['analysisFramework']
        self.assertEqual(response, None, response)
        # Shouldn't work for non-member private AF even if there is a project attached
        project = ProjectFactory.create(analysis_framework=private_af)
        response = self.query_check(query, variables={'id': private_af.pk})['data']['analysisFramework']
        self.assertEqual(response, None, response)
        # Should work for member private AF
        project.add_member(user)
        response = self.query_check(query, variables={'id': private_af.pk})['data']['analysisFramework']
        self.assertIdEqual(response['id'], private_af.id, response)
        self.assertEqual(response['isPrivate'], True, response)

    def test_analysis_framework_detail_query(self):
        query = '''
            query MyQuery ($id: ID!) {
              analysisFramework(id: $id) {
                id
                currentUserRole
                description
                isPrivate
                title
                secondaryTagging {
                  id
                  key
                  title
                  widgetId
                  order
                  properties
                }
                primaryTagging {
                  id
                  title
                  order
                  tooltip
                  widgets {
                    id
                    key
                    title
                    widgetId
                    order
                    properties
                  }
                }
               members {
                  id
                  joinedAt
                  addedBy {
                    id
                    displayName
                  }
                  member {
                    id
                    displayName
                  }
                  role {
                    id
                    title
                  }
                }
              }
            }
        '''

        user = UserFactory.create()
        another_user = UserFactory.create()
        af = AnalysisFrameworkFactory.create()
        af.add_member(another_user)

        def _query_check(**kwargs):
            return self.query_check(query, variables={'id': af.pk}, **kwargs)

        # Without login
        _query_check(assert_for_error=True)

        # With login
        self.force_login(user)

        # Should work for normal AF
        response = _query_check()['data']['analysisFramework']
        self.assertEqual(len(response['secondaryTagging']), 0, response)
        self.assertEqual(len(response['primaryTagging']), 0, response)

        # Let's add some widgets and sections
        sequence = factory.Sequence(lambda n: n)
        rsequence = factory.Sequence(lambda n: 20 - n)
        # Primary Tagging
        for order, widget_count, tooltip, _sequence in (
            (3, 2, 'Some tooltip info 101', sequence),
            (1, 3, 'Some tooltip info 102', rsequence),
            (2, 4, 'Some tooltip info 103', sequence),
        ):
            section = SectionFactory.create(analysis_framework=af, order=order, tooltip=tooltip)
            WidgetFactory.create_batch(widget_count, analysis_framework=af, section=section, order=_sequence)
            WidgetFactory.reset_sequence()
        # Secondary Tagging
        WidgetFactory.create_batch(4, analysis_framework=af, order=rsequence)

        # Let's save/compare snapshot (without membership)
        response = _query_check()
        self.assertMatchSnapshot(response, 'without-membership')

        # Let's save/compare snapshot (with membership)
        af.add_member(user)
        response = _query_check()
        self.assertMatchSnapshot(response, 'with-membership')


class TestAnalysisFrameworkMutationSnapShotTestCase(GraphQLSnapShotTestCase):
    def setUp(self):
        super().setUp()
        self.create_query = '''
            mutation MyMutation ($input: AnalysisFrameworkInputType!) {
              __typename
              analysisFrameworkCreate(data: $input) {
                ok
                errors
                result {
                  id
                  isPrivate
                  description
                  currentUserRole
                  title
                  primaryTagging {
                    id
                    order
                    title
                    tooltip
                    clientId
                    widgets {
                      id
                      key
                      order
                      properties
                      title
                      widgetId
                      clientId
                    }
                  }
                  secondaryTagging {
                    id
                    key
                    order
                    properties
                    title
                    widgetId
                    clientId
                  }
                }
              }
            }
        '''

        self.organization1 = OrganizationFactory.create()
        self.invalid_minput = dict(
            title='',
            description='Af description',
            isPrivate=False,
            organization=str(self.organization1.id),
            # previewImage='',
            primaryTagging=[
                dict(
                    title='',
                    clientId='section-101',
                    order=2,
                    tooltip='Tooltip for section 101',
                    widgets=[
                        dict(
                            clientId='section-text-101-client-id',
                            title='',
                            widgetId=self.genum(Widget.WidgetType.TEXT),
                            key='section-text-101',
                            order=1,
                            properties=dict(),
                        ),
                        dict(
                            clientId='section-text-102-client-id',
                            title='',
                            widgetId=self.genum(Widget.WidgetType.TEXT),
                            key='section-text-102',
                            order=2,
                            properties=dict(),
                        ),
                    ],
                ),
                dict(
                    title='',
                    clientId='section-102',
                    order=1,
                    tooltip='Tooltip for section 102',
                    widgets=[
                        dict(
                            clientId='section-2-text-101-client-id',
                            title='Section-2-Text-101',
                            widgetId=self.genum(Widget.WidgetType.TEXT),
                            key='section-2-text-101',
                            order=1,
                            properties=dict(),
                        ),
                        dict(
                            clientId='section-2-text-102-client-id',
                            title='Section-2-Text-102',
                            widgetId=self.genum(Widget.WidgetType.TEXT),
                            key='section-2-text-102',
                            order=2,
                            properties=dict(),
                        ),
                    ],
                ),
            ],
            secondaryTagging=[
                dict(
                    clientId='select-widget-101-client-id',
                    title='',
                    widgetId=self.genum(Widget.WidgetType.SELECT),
                    key='select-widget-101-key',
                    order=1,
                    properties=dict(),
                ),
                dict(
                    clientId='multi-select-widget-102-client-id',
                    title='multi-select-Widget-2',
                    widgetId=self.genum(Widget.WidgetType.MULTISELECT),
                    key='multi-select-widget-102-key',
                    order=2,
                    properties=dict(),
                ),
            ],
        )

        self.valid_minput = dict(
            title='AF (TEST)',
            description='Af description',
            isPrivate=False,
            organization=str(self.organization1.id),
            # previewImage='',
            primaryTagging=[
                dict(
                    title='Section 101',
                    clientId='section-101',
                    order=2,
                    tooltip='Tooltip for section 101',
                    widgets=[
                        dict(
                            clientId='section-text-101-client-id',
                            title='Section-Text-101',
                            widgetId=self.genum(Widget.WidgetType.TEXT),
                            key='section-text-101',
                            order=1,
                            properties=dict(),
                        ),
                        dict(
                            clientId='section-text-102-client-id',
                            title='Section-Text-102',
                            widgetId=self.genum(Widget.WidgetType.TEXT),
                            key='section-text-102',
                            order=2,
                            properties=dict(),
                        ),
                    ],
                ),
                dict(
                    title='Section 102',
                    clientId='section-102',
                    order=1,
                    tooltip='Tooltip for section 102',
                    widgets=[
                        dict(
                            clientId='section-2-text-101-client-id',
                            title='Section-2-Text-101',
                            widgetId=self.genum(Widget.WidgetType.TEXT),
                            key='section-2-text-101',
                            order=1,
                            properties=dict(),
                        ),
                        dict(
                            clientId='section-2-text-102-client-id',
                            title='Section-2-Text-102',
                            widgetId=self.genum(Widget.WidgetType.TEXT),
                            key='section-2-text-102',
                            order=2,
                            properties=dict(),
                        ),
                    ],
                ),
            ],
            secondaryTagging=[
                dict(
                    clientId='select-widget-101-client-id',
                    title='Select-Widget-1',
                    widgetId=self.genum(Widget.WidgetType.SELECT),
                    key='select-widget-101-key',
                    order=1,
                    properties=dict(),
                ),
                dict(
                    clientId='multi-select-widget-102-client-id',
                    title='multi-select-Widget-2',
                    widgetId=self.genum(Widget.WidgetType.MULTISELECT),
                    key='multi-select-widget-102-key',
                    order=2,
                    properties=dict(),
                ),
            ],
        )

    def test_analysis_framework_create(self):
        user = UserFactory.create()

        def _query_check(minput, **kwargs):
            return self.query_check(self.create_query, minput=minput, **kwargs)

        # Without login
        _query_check(self.valid_minput, assert_for_error=True)

        # With login
        self.force_login(user)

        response = _query_check(self.invalid_minput, okay=False)
        self.assertMatchSnapshot(response, 'errors')

        response = _query_check(self.valid_minput, okay=True)
        self.assertMatchSnapshot(response, 'success')

    def test_analysis_framework_update(self):
        query = '''
            mutation MyMutation ($id: ID! $input: AnalysisFrameworkInputType!) {
              __typename
              analysisFramework (id: $id ) {
                  analysisFrameworkUpdate(data: $input) {
                    ok
                    errors
                    result {
                      id
                      isPrivate
                      description
                      currentUserRole
                      title
                      primaryTagging {
                        id
                        order
                        title
                        tooltip
                        clientId
                        widgets {
                          id
                          key
                          order
                          properties
                          title
                          widgetId
                          clientId
                        }
                      }
                      secondaryTagging {
                        id
                        key
                        order
                        properties
                        title
                        widgetId
                        clientId
                      }
                    }
                  }
              }
            }
        '''

        user = UserFactory.create()

        def _query_check(id, minput, **kwargs):
            return self.query_check(
                query,
                minput=minput,
                mnested=['analysisFramework'],
                variables={'id': id},
                **kwargs,
            )
        # ---------- Without login
        _query_check(0, self.valid_minput, assert_for_error=True)
        # ---------- With login
        self.force_login(user)
        # ---------- Let's create a new AF (Using create test data)
        new_af_response = self.query_check(
            self.create_query, minput=self.valid_minput)['data']['analysisFrameworkCreate']['result']
        new_af_id = new_af_response['id']
        # ---------------- Remove invalid attributes
        new_af_response.pop('currentUserRole')
        new_af_response.pop('id')
        # ---------- Let's change some attributes (for validation errors)
        new_af_response['title'] = ''
        new_af_response['primaryTagging'][0]['title'] = ''
        # ----------------- Let's try to update
        response = _query_check(new_af_id, new_af_response, okay=False)
        self.assertMatchSnapshot(response, 'errors')
        # ---------- Let's change some attributes (for success change)
        new_af_response['title'] = 'Updated AF (TEST)'
        new_af_response['description'] = 'Updated Af description'
        new_af_response['primaryTagging'][0]['title'] = 'Updated Section 102'
        new_af_response['primaryTagging'][0]['widgets'][0].pop('id')  # Remove/Create a widget
        new_af_response['primaryTagging'][0]['widgets'][1]['title'] = 'Updated-Section-2-Text-101'  # Remove a widget
        new_af_response['primaryTagging'][1].pop('id')  # Remove/Create second ordered section (but use current widgets)
        new_af_response['secondaryTagging'].pop(0)  # Remove another widget
        new_af_response['secondaryTagging'][0].pop('id')  # Remove/Create another widget
        # ----------------- Let's try to update
        response = _query_check(new_af_id, new_af_response, okay=True)
        self.assertMatchSnapshot(response, 'success')

        another_user = UserFactory.create()
        self.force_login(another_user)
        _query_check(new_af_id, new_af_response, assert_for_error=True)

    def test_analysis_framework_membership_bulk(self):
        query = '''
          mutation MyMutation(
              $id: ID!,
              $afMembership: [BulkAnalysisFrameworkMembershipInputType!]!,
              $afMembershipDelete: [ID!]!
          ) {
          __typename
          analysisFramework(id: $id) {
            id
            title
            analysisFrameworkMembershipBulk(items: $afMembership, deleteIds: $afMembershipDelete) {
              errors
              result {
                id
                clientId
                joinedAt
                addedBy {
                  id
                  displayName
                }
                role {
                  id
                  title
                }
                member {
                  id
                  displayName
                }
              }
              deletedResult {
                id
                clientId
                joinedAt
                member {
                  id
                  displayName
                }
                role {
                  id
                  title
                }
                addedBy {
                  id
                  displayName
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
        af = AnalysisFrameworkFactory.create(created_by=creater_user)
        membership1, _ = af.add_member(member_user1)
        membership2, _ = af.add_member(member_user2)
        creater_user_membership, _ = af.add_member(creater_user, role=self.af_owner)
        user_membership, _ = af.add_member(user, role=self.af_owner)
        af.add_member(low_permission_user)

        minput = dict(
            afMembershipDelete=[
                str(membership1.pk),  # This will be only on try 1
                # This shouldn't be on any response (requester + creater)
                str(user_membership.pk),
                str(creater_user_membership.pk),
            ],
            afMembership=[
                # Try updating membership (Valid)
                dict(
                    member=member_user2.pk,
                    clientId="member-user-2",
                    role=self.af_owner.pk,
                    id=membership2.pk,
                ),
                # Try adding already existing member (Invalid on try 1, valid on try 2)
                dict(
                    member=member_user1.pk,
                    clientId="member-user-1",
                    role=self.af_default.pk,
                ),
                # Try adding new member (Valid on try 1, invalid on try 2)
                dict(
                    member=member_user3.pk,
                    clientId="member-user-3",
                    role=self.af_default.pk,
                ),
                # Try adding new member (without giving role) -> this should use default role
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
                mnested=['analysisFramework'],
                variables={'id': af.id, **minput},
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
        response = _query_check()['data']['analysisFramework']['analysisFrameworkMembershipBulk']
        self.assertMatchSnapshot(response, 'try 1')
        # ----------------- All valid input
        response = _query_check()['data']['analysisFramework']['analysisFrameworkMembershipBulk']
        self.assertMatchSnapshot(response, 'try 2')

    @mock.patch('analysis_framework.serializers.AfWidgetLimit')
    def test_widgets_limit(self, AfWidgetLimitMock):
        query = '''
            mutation MyMutation ($input: AnalysisFrameworkInputType!) {
              __typename
              analysisFrameworkCreate(data: $input) {
                ok
                errors
                result {
                  id
                }
              }
            }
        '''

        user = UserFactory.create()

        minput = dict(
            title='AF (TEST)',
            primaryTagging=[
                dict(
                    title=f'Section {i}',
                    clientId=f'section-{i}',
                    order=i,
                    tooltip=f'Tooltip for section {i}',
                    widgets=[
                        dict(
                            clientId=f'section-text-{j}-client-id',
                            title=f'Section-Text-{j}',
                            widgetId=self.genum(Widget.WidgetType.TEXT),
                            key=f'section-text-{j}',
                            order=j,
                        )
                        for j in range(0, 4)
                    ],
                ) for i in range(0, 2)
            ],
            secondaryTagging=[
                dict(
                    clientId=f'section-text-{j}-client-id',
                    title=f'Section-Text-{j}',
                    widgetId=self.genum(Widget.WidgetType.TEXT),
                    key=f'section-text-{j}',
                    order=j,
                )
                for j in range(0, 4)
            ],
        )

        self.force_login(user)

        def _query_check(**kwargs):
            return self.query_check(query, minput=minput, **kwargs)['data']['analysisFrameworkCreate']

        # Let's change the limit to lower value for easy testing :P
        AfWidgetLimitMock.MAX_SECTIONS_ALLOWED = 1
        AfWidgetLimitMock.MAX_WIDGETS_ALLOWED_PER_SECTION = 2
        AfWidgetLimitMock.MAX_WIDGETS_ALLOWED_IN_SECONDARY_TAGGING = 2
        response = _query_check(okay=False)
        self.assertMatchSnapshot(response, 'failure-widget-level')
        # Let's change the limit to lower value for easy testing :P
        AfWidgetLimitMock.MAX_WIDGETS_ALLOWED_IN_SECONDARY_TAGGING = 10
        AfWidgetLimitMock.MAX_WIDGETS_ALLOWED_PER_SECTION = 10
        response = _query_check(okay=False)
        self.assertMatchSnapshot(response, 'failure-section-level')
        # Let's change the limit to higher value
        # Let's change the limit to higher value
        AfWidgetLimitMock.MAX_SECTIONS_ALLOWED = 5
        _query_check(okay=True)


class TestAnalysisFrameworkCreateUpdate(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.create_mutation = '''
        mutation Mutation($input: AnalysisFrameworkInputType!) {
          analysisFrameworkCreate(data: $input) {
            ok
            errors
            result {
              id
              title
              isPrivate
              description
            }
          }
        }
        '''
        self.update_mutation = '''
        mutation UpdateMutation($input: AnalysisFrameworkInputType!, $id: ID!) {
            analysisFramework (id: $id ) {
              analysisFrameworkUpdate(data: $input) {
                ok
                errors
                result {
                  id
                  title
                  isPrivate
                  description
                }
              }
          }
        }
        '''

    def test_create_analysis_framework(self):
        self.input = dict(
            title='new title'
        )
        self.force_login(self.user)

        response = self.query(
            self.create_mutation,
            input_data=self.input
        )
        self.assertResponseNoErrors(response)

        content = response.json()
        self.assertTrue(content['data']['analysisFrameworkCreate']['ok'], content)
        self.assertEqual(
            content['data']['analysisFrameworkCreate']['result']['title'],
            self.input['title']
        )

    # TODO: MOVE THIS TO PROJECT TEST
    # def test_create_private_framework_unauthorized(self):
    #     project = ProjectFactory.create()
    #     project.add_member(self.user)
    #     self.input = dict(
    #         title='new title',
    #         isPrivate=True,
    #         project=project.id,
    #     )
    #     self.force_login(self.user)
    #     response = self.query(
    #         self.create_mutation,
    #         input_data=self.input
    #     )
    #     content = response.json()
    #     self.assertIsNotNone(content['errors'][0]['message'])
    #     # The actual message is
    #     # You don't have permissions to create private framework
    #     self.assertIn('permission', content['errors'][0]['message'])

    # def test_invalid_create_framework_privately_in_public_project(self):
    #     project = ProjectFactory.create(is_private=False)
    #     project.add_member(self.user)
    #     self.assertEqual(project.is_private, False)

    #     self.input = dict(
    #         title='new title',
    #         isPrivate=True,
    #         project=project.id,
    #     )
    #     self.force_login(self.user)

    #     response = self.query(
    #         self.create_mutation,
    #         input_data=self.input
    #     )
    #     content = response.json()
    #     self.assertIsNotNone(content['errors'][0]['message'])
    #     self.assertIn('permission', content['errors'][0]['message'])

    def test_change_is_private_field(self):
        """Even the owner should be unable to change privacy"""
        private_framework = AnalysisFrameworkFactory.create(is_private=True)
        public_framework = AnalysisFrameworkFactory.create(is_private=False)
        user = self.user
        private_framework.add_member(
            user,
            private_framework.get_or_create_owner_role()
        )
        public_framework.add_member(
            user,
            public_framework.get_or_create_owner_role()
        )
        content = self._change_framework_privacy(public_framework, user)
        self.assertIsNotNone(content['errors'][0]['message'])
        self.assertIn('permission', content['errors'][0]['message'])
        content = self._change_framework_privacy(private_framework, user)
        self.assertIsNotNone(content['errors'][0]['message'])
        self.assertIn('permission', content['errors'][0]['message'])

    def test_change_other_fields(self):
        private_framework = AnalysisFrameworkFactory.create(is_private=True)
        public_framework = AnalysisFrameworkFactory.create(is_private=False)
        user = self.user
        private_framework.add_member(
            user,
            private_framework.get_or_create_owner_role()
        )
        public_framework.add_member(
            user,
            public_framework.get_or_create_owner_role()
        )

        self.force_login(user)

        # private framework update
        self.input = dict(
            title='new title updated',
            isPrivate=private_framework.is_private,
        )
        response = self.query(
            self.update_mutation,
            input_data=self.input,
            variables={'id': private_framework.id},
        )
        private_framework.refresh_from_db()
        content = response.json()
        self.assertNotEqual(content['data']['analysisFramework']['analysisFrameworkUpdate'], None, content)
        self.assertTrue(content['data']['analysisFramework']['analysisFrameworkUpdate']['ok'], content)
        self.assertEqual(
            private_framework.title,
            self.input['title']
        )

        # public framework update
        self.input = dict(
            title='public title updated',
            isPrivate=public_framework.is_private,
        )
        response = self.query(
            self.update_mutation,
            input_data=self.input,
            variables={'id': public_framework.id},
        )
        public_framework.refresh_from_db()
        content = response.json()
        self.assertNotEqual(content['data']['analysisFramework']['analysisFrameworkUpdate'], None, content)
        self.assertTrue(content['data']['analysisFramework']['analysisFrameworkUpdate']['ok'], content)
        self.assertEqual(
            public_framework.title,
            self.input['title']
        )

    def _change_framework_privacy(self, framework, user):
        self.force_login(user)

        changed_privacy = not framework.is_private
        self.input = dict(
            title='new title',
            isPrivate=changed_privacy,
            # other fields not cared for now
        )
        response = self.query(
            self.update_mutation,
            input_data=self.input,
            variables={'id': framework.id},
        )
        content = response.json()
        return content

    def test_af_modified_at(self):
        create_mutation = '''
        mutation Mutation($input: AnalysisFrameworkInputType!) {
          analysisFrameworkCreate(data: $input) {
            ok
            errors
            result {
              id
              title
              isPrivate
              description
              modifiedAt
            }
          }
        }
        '''
        update_mutation = '''
        mutation UpdateMutation($input: AnalysisFrameworkInputType!, $id: ID!) {
            analysisFramework (id: $id ) {
              analysisFrameworkUpdate(data: $input) {
                ok
                errors
                result {
                  id
                  title
                  isPrivate
                  description
                  modifiedAt
                }
              }
          }
        }
        '''

        self.force_login(self.user)

        # Create
        minput = dict(title='new title')
        af_response = self.query_check(create_mutation, minput=minput)['data']['analysisFrameworkCreate']['result']
        af_id = af_response['id']
        af_modified_at = af_response['modifiedAt']

        # Update
        minput = dict(title='new updated title')
        updated_af_response = self.query_check(
            update_mutation, minput=minput, variables={'id': af_id}
        )['data']['analysisFramework']['analysisFrameworkUpdate']['result']
        # Make sure modifiedAt is higher now
        assert updated_af_response['modifiedAt'] > af_modified_at
