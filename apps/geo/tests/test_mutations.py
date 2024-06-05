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
        project_member_user = UserFactory.create()
        non_project_member_user = UserFactory.create()
        project = ProjectFactory.create(
            created_by=project_member_user
        )
        project.add_member(project_member_user)

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

        # with login with project_member_user
        self.force_login(project_member_user)

        content = _query_check(minput)
        self.assertIn(project_member_user, project.members.all())
        self.assertEqual(content['data']['createRegion']['errors'], None)
        self.assertEqual(content['data']['createRegion']['result']['title'], "Test")

        # make sure region is attached with project
        self.assertIn(
            Region.objects.get(id=content['data']['createRegion']['result']['id']), project.regions.all()
        )

        #  make sure region is not pubhished
        self.assertEqual(
            Region.objects.get(id=content['data']['createRegion']['result']['id']).is_published, False
        )

        # login with non_project_member_user
        self.force_login(non_project_member_user)
        content = _query_check(minput)
        self.assertNotIn(non_project_member_user, project.members.all())
        self.assertEqual(content['data']['createRegion']['errors'][0]['messages'], "Permission Denied")
