import factory

from utils.graphene.tests import GraphQLTestCase, GraphQLSnapShotTestCase

from user.factories import UserFactory
from project.factories import ProjectFactory
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

    def test_analysis_framework_widgets(self):
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
                  widgets {
                    id
                    key
                    title
                    widgetId
                    order
                    properties
                  }
                }
              }
            }
        '''

        user = UserFactory.create()
        af = AnalysisFrameworkFactory.create()

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
        for order, widget_count, _sequence in (
            (3, 2, sequence),
            (1, 5, rsequence),
            (2, 3, sequence),
        ):
            section = SectionFactory.create(analysis_framework=af, order=order)
            WidgetFactory.create_batch(widget_count, analysis_framework=af, section=section, order=_sequence)
            WidgetFactory.reset_sequence()
        # Secondary Tagging
        WidgetFactory.create_batch(4, analysis_framework=af, order=rsequence)

        # Let's save/compare snapshot
        response = _query_check()
        self.assertMatchSnapshot(response)


class TestAnalysisFrameworkCreateUpdate(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.create_mutation = '''
        mutation Mutation($input: AnalysisFrameworkInputType!) {
          createAnalysisFramework(data: $input) {
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
          updateAnalysisFramework(data: $input, id: $id) {
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
        self.assertTrue(content['data']['createAnalysisFramework']['ok'], content)
        self.assertEqual(
            content['data']['createAnalysisFramework']['result']['title'],
            self.input['title']
        )

    def test_create_private_framework_unauthorized(self):
        project = ProjectFactory.create()
        project.add_member(self.user)
        self.input = dict(
            title='new title',
            isPrivate=True,
            project=project.id,
        )
        self.force_login(self.user)
        response = self.query(
            self.create_mutation,
            input_data=self.input
        )
        content = response.json()
        self.assertIsNotNone(content['errors'][0]['message'])
        # The actual message is
        # You don't have permissions to create private framework
        self.assertIn('permission', content['errors'][0]['message'])

    def test_invalid_create_framework_privately_in_public_project(self):
        project = ProjectFactory.create(is_private=False)
        project.add_member(self.user)
        self.assertEqual(project.is_private, False)

        self.input = dict(
            title='new title',
            isPrivate=True,
            project=project.id,
        )
        self.force_login(self.user)

        response = self.query(
            self.create_mutation,
            input_data=self.input
        )
        content = response.json()
        self.assertIsNotNone(content['errors'][0]['message'])
        self.assertIn('permission', content['errors'][0]['message'])

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
        self.assertTrue(content['data']['updateAnalysisFramework']['ok'], content)
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
        self.assertTrue(content['data']['updateAnalysisFramework']['ok'], content)
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
