from utils.graphene.tests import GraphqlTestCase


class AnalysisFrameworkTests(GraphqlTestCase):
    def setUp(self):
        super().setUp()
        self.create_mutation = '''
        mutation Mutation($input: AnalysisFrameworkInputType!) {
          createAnalysisFramework(data: $input) {
            ok
            errors
            result {
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
        self.force_login()

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

    def test_get_private_analysis_framework_not_member(self):
        pass

    def test_get_private_analysis_framework_not_member_but_same_project(self):
        pass

    def test_get_related_to_me_frameworks(self):
        pass

    def test_get_private_analysis_framework_by_member(self):
        pass

    def test_get_public_framework_with_roles(self):
        pass

    def test_get_memberships(self):
        pass

    def test_clone_analysis_framework_without_name(self):
        pass

    def test_clone_analysis_framework(self):
        pass

    def test_create_private_framework_unauthorized(self):
        pass

    def test_create_private_framework(self):
        pass

    def test_change_is_private_field(self):
        pass

    def test_change_other_fields(self):
        pass

    def test_get_membersips(self):
        pass

    def test_add_roles_to_public_framework_non_member(self):
        pass

    def test_project_analysis_framework(self):
        pass

    def test_filter_analysis_framework(self):
        pass

    def test_search_users_excluding_framework_members(self):
        pass

    def test_af_project_api(self):
        pass

    def check_owner_roles_present(self, framework, permissions):
        pass

    def check_default_roles_present(self, framework, permissions):
        pass
