from user.factories import UserFactory
from project.factories import ProjectFactory
from utils.graphene.tests import GraphQLTestCase

from geo.models import Region


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
        user2 = UserFactory.create()
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

        minput = dict(
            project=project.id,
            code="NPL",
            title="Test",
        )
        # without login
        _query_check(minput, assert_for_error=True)

        # with login
        self.force_login(user)

        content = _query_check(minput)
        self.assertIn(user, project.members.all())
        self.assertEqual(content['data']['createRegion']['errors'], None)
        self.assertEqual(content['data']['createRegion']['result']['title'], "Test")
        self.assertIn(
            Region.objects.get(id=content['data']['createRegion']['result']['id']), project.regions.all()
        )

        # login normal user
        self.force_login(user2)
        content = _query_check(minput)
        self.assertNotIn(user2, project.members.all())
        self.assertEqual(content['data']['createRegion']['errors'][0]['messages'], "Permission Denied")
