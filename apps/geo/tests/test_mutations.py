from geo.factories import RegionFactory
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
            created_by=user
        )
        project.add_member(user)

        def _query_check(minput, **kwargs):
            return self.query_check(
                self.region_query,
                minput=minput,
                **kwargs
            )

        minput = {
            'project': project.id,
            'code': 'NPL',
            'title': 'Test'
        }
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


class RemoveRegionFromProjectTestMutation(GraphQLTestCase):
    def test_remove_region_from_project(self):
        self.remove_region_query = '''
            mutation MyMutation($projectId: ID!, $regionId: ID!) {
                removeProjectRegion(id: $regionId, projectid: $projectId) {
                    ok
                    errors
                }
            }
        '''

        user = UserFactory.create()
        region = RegionFactory()
        project = ProjectFactory(created_by=user)
        project.add_member(user)
        project.regions.add(region)

        def _query_check(minput, **kwargs):
            return self.query_check(
                self.remove_region_query,
                variable={
                    'projectId': project.id,
                    'regionId': region.id
                },
                **kwargs
            )

        # Without login
        minput = {
            'projectId': project.id,
            'regionId': region.id
        }
        _query_check(minput, assert_for_error=True)

        # With login
        self.force_login(user)
        content = _query_check(minput)
        self.assertTrue(content['data']['removeProjectRegion']['ok'])
        self.assertIsNone(content['data']['removeProjectRegion']['errors'])

        # Ensure region is removed from the project
        project.refresh_from_db()
        self.assertNotIn(region, project.regions.all())

        # Login as a different user
        user2 = UserFactory.create()
        self.force_login(user2)
        # Provide the required variables again
        minput = {
            'projectId': project.id,
            'regionId': region.id
        }
        content = _query_check(minput)
        self.assertFalse(content['data']['removeProjectRegion']['ok'])
        self.assertEqual(content['data']['removeProjectRegion']['errors'][0]['messages'], "Permission Denied")
