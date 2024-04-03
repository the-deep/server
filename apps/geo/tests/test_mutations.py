from user.factories import UserFactory
from project.factories import ProjectFactory
from utils.graphene.tests import GraphQLTestCase


class CreateTestMutation(GraphQLTestCase):
    def test_create_region_in_project(self):
        self.region_query = '''
            mutation MyMutation($input: RegionInputType!){
              createRegion(data: $input) {
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
        project = ProjectFactory.create(
            title="dummy project 1",
            created_by=user
        )
        project.add_member(user)

        def _query_check(minput, **kwargs):
            return self.query_check(
                self.region_query,
                minput=minput,
                **kwargs
            )
    # -- Without login

        minput = dict(
            project=project.id,
            code="NPL",
            title="Test",
        )
        # without login
        _query_check(minput, assert_for_error=True)

        self.force_login(user)

        _query_check(minput)
        content = _query_check(minput)
        self.assertEqual(content['data']['createRegion']['errors'], None)
        self.assertEqual(content['data']['createRegion']['result']['title'], "Test")
