from user.factories import UserFactory
from project.factories import ProjectFactory
from utils.graphene.tests import GraphQLTestCase

from geo.models import Region
from geo.factories import RegionFactory, AdminLevelFactory


class CreateTestMutation(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.other_user = UserFactory.create()
        self.region = RegionFactory.create(
            created_by=self.user
        )

    def test_add_admin_level(self):
        self.add_admin_level_query = '''

            mutation MyMutation($input: AdminLevelInputType!){
              createAdminLevel(data: $input) {
                ok
                errors
                result {
                  codeProp
                  id
                  level
                  nameProp
                  parent
                  parentCodeProp
                  parentNameProp
                  staleGeoAreas
                  title
                  tolerance
                }
              }
            }
        '''

        def _query_check(minput, **kwargs):
            return self.query_check(
                self.add_admin_level_query,
                minput=minput,
                **kwargs
            )
        minput = {
            'region': self.region.id,
            'title': "Test-admin-level"
        }

        # without login user
        _query_check(minput, assert_for_error=True)

        # with normal user
        self.force_login(self.user)
        content = _query_check(minput)['data']['createAdminLevel']['result']
        self.assertEqual(content['title'], minput['title'], content)

        # with other_user
        self.force_login(self.other_user)
        content = _query_check(minput, okay=False)

        # with login user
        # when region is published
        self.region.is_published = True
        self.region.save(update_fields=['is_published'])
        self.force_login(self.user)
        _query_check(minput, okay=False)

        # with other user
        self.force_login(self.other_user)
        _query_check(minput, okay=False)

    def test_update_admin_level(self):
        update_admin_level_query = '''
            mutation MyMutation($adminLevelId:ID! $input:AdminLevelInputType!){
                updateAdminLevel(id: $adminLevelId data:$input){
                    ok
                    errors
                    result {
                      codeProp
                      id
                      level
                      nameProp
                      parent
                      parentCodeProp
                      parentNameProp
                      staleGeoAreas
                      title
                      tolerance
                    }
                }
            }
        '''
        admin_level = AdminLevelFactory.create(
            region=self.region
        )

        minput = {
            "title": "Update Admin Level",
            "region": self.region.id
        }

        def _query_check(minput, **kwargs):
            return self.query_check(
                update_admin_level_query,
                minput=minput,
                variables={'adminLevelId': admin_level.id},
                **kwargs
            )

        # without login
        _query_check(minput, assert_for_error=True)

        # with normal user
        self.force_login(self.user)
        content = _query_check(minput)['data']['updateAdminLevel']['result']
        self.assertEqual(content['title'], minput['title'], content)
        admin_level.refresh_from_db()

        self.assertEqual(admin_level.title, minput['title'])

        # login with other user
        self.force_login(self.other_user)
        minput['title'] = "Reupdated Admin Level"
        _query_check(minput, okay=False)
        self.assertNotEqual(admin_level.title, minput['title'])

        # login with normal user
        # when region is published
        self.region.is_published = True
        self.region.save(update_fields=['is_published'])
        self.force_login(self.user)
        _query_check(minput, okay=False)

        # login with other user
        # when region is published
        self.force_login(self.other_user)
        _query_check(minput, okay=False)

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

    def test_publish_region(self):
        self.publish_region_query = '''
            mutation MyMutation($id:ID!){
                publishRegion(id: $id) {
                    ok
                    errors
                }
            }
        '''
        user = UserFactory.create()
        other_user = UserFactory.create()
        project = ProjectFactory.create()
        region = RegionFactory.create(created_by=user)
        project.add_member(user)

        def _query_check(**kwargs):
            return self.query_check(
                self.publish_region_query,
                variables={'id': region.id},
                **kwargs
            )

        # without login user
        _query_check(assert_for_error=True)

        # login with user
        self.force_login(user)
        content = _query_check()
        region.refresh_from_db()
        self.assertEqual(content['data']['publishRegion']['errors'], None)
        self.assertEqual(region.is_published, True)

        # login with other user
        self.force_login(other_user)
        content = _query_check()
        self.assertEqual(
            content['data']['publishRegion']['errors'][0]['messages'],
            'Authorized User can only published the region'
        )
