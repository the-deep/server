from utils.graphene.tests import GraphQLTestCase

from analysis_framework.models import AnalysisFramework

from user.factories import UserFactory
from analysis_framework.factories import AnalysisFrameworkFactory
from project.factories import ProjectFactory


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
