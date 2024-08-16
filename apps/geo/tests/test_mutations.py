from user.factories import UserFactory
from project.factories import ProjectFactory
from utils.graphene.tests import GraphQLTestCase

from geo.models import Region
from geo.factories import RegionFactory, AdminLevelFactory


class CreateAdminLevelTestMutation(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.other_user = UserFactory.create()
        self.region = RegionFactory.create(
            created_by=self.user
        )

    def test_add_admin_level(self):
        mutation_query = '''

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
                mutation_query,
                minput=minput,
                **kwargs
            )

        minput = {
            'region': str(self.region.id),
            'title': "Test-admin-level"
        }

        # without login user
        _query_check(minput, assert_for_error=True)

        # with normal user
        # when region is published
        region = RegionFactory.create(
            created_by=self.user,
            is_published=True
        )
        self.force_login(self.user)
        minput['region'] = region.id
        _query_check(minput, okay=False)

        # with other user
        self.force_login(self.other_user)
        _query_check(minput, okay=False)

        # with normal user
        minput['region'] = self.region.id
        self.force_login(self.user)
        content = _query_check(minput)['data']['createAdminLevel']['result']
        self.assertEqual(content['title'], minput['title'], content)

    def test_update_admin_level(self):
        mutation_query = '''
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
            "region": str(self.region.id)
        }

        def _query_check(minput, **kwargs):
            return self.query_check(
                mutation_query,
                minput=minput,
                variables={'adminLevelId': admin_level.id},
                **kwargs
            )

        # without login
        _query_check(minput, assert_for_error=True)

        # login with other user
        self.force_login(self.other_user)
        minput['title'] = "Reupdated Admin Level"
        _query_check(minput, okay=False)
        self.assertNotEqual(admin_level.title, minput['title'])

        # login with normal user but region is published

        region = RegionFactory.create(
            created_by=self.user,
            is_published=True
        )
        minput['region'] = str(region.id)
        self.force_login(self.user)
        _query_check(minput, okay=False)

        # login with other user
        # when region is published
        minput['region'] = str(self.region.id)
        self.force_login(self.other_user)
        _query_check(minput, okay=False)

        # with normal user
        self.force_login(self.user)
        content = _query_check(minput)['data']['updateAdminLevel']['result']
        self.assertEqual(content['title'], minput['title'], content)
        admin_level.refresh_from_db()
        self.assertEqual(admin_level.title, minput['title'])


class CreateRegionTestMutation(GraphQLTestCase):

    def setUp(self):
        super().setUp()
        self.non_project_member_user = UserFactory.create()
        self.project_member_user = UserFactory.create()
        self.region = RegionFactory.create(
            created_by=self.project_member_user
        )
        self.project = ProjectFactory.create(
            created_by=self.project_member_user
        )
        self.project.add_member(self.project_member_user)

    def test_create_region_in_project(self):
        mutation_query = '''
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

        def _query_check(minput, **kwargs):
            return self.query_check(
                mutation_query,
                minput=minput,
                **kwargs
            )

        minput = {
            'project': str(self.project.id),
            'code': 'NPL',
            'title': 'Test'
        }
        # without login
        _query_check(minput, assert_for_error=True)

        # login with non_project_member_user
        self.force_login(self.non_project_member_user)
        content = _query_check(minput)
        self.assertNotIn(self.non_project_member_user, self.project.members.all())
        self.assertEqual(content['data']['createRegion']['errors'][0]['messages'], "You Don't have permission in project")

        # with login with project_member_user
        self.force_login(self.project_member_user)
        content = _query_check(minput)
        self.assertIn(self.project_member_user, self.project.members.all())
        self.assertEqual(content['data']['createRegion']['errors'], None)
        self.assertEqual(content['data']['createRegion']['result']['title'], "Test")

        # make sure region is attached with project
        self.assertIn(
            Region.objects.get(id=content['data']['createRegion']['result']['id']), self.project.regions.all()
        )

        #  make sure region is not pubhished
        self.assertEqual(
            Region.objects.get(id=content['data']['createRegion']['result']['id']).is_published, False
        )

    def test_update_region_mutation(self):
        mutation_query = '''
                mutation MyMutation($id: ID! $input:RegionInputType!) {
                    updateRegion(id: $id data:$input) {
                        ok
                        errors
                        result {
                            centroid
                            clientId
                            id
                            isPublished
                            keyFigures
                            mediaSources
                            populationData
                            public
                            regionalGroups
                            title
                        }
                    }
                }
        '''

        def _query_check(minput, **kwargs):
            return self.query_check(
                mutation_query,
                minput=minput,
                **kwargs
            )

        minput = {
            'project': self.project.id,
            "title": "Updated Region",
            "code": "123",
        }

        # without login
        _query_check(minput, variables={'id': self.region.id}, assert_for_error=True)

        # with non project memeber
        self.force_login(self.non_project_member_user)
        content = _query_check(minput, variables={'id': self.region.id}, okay=False)

        # with login with user and region is published

        region = RegionFactory.create(
            created_by=self.project_member_user,
            is_published=True
        )

        self.force_login(self.project_member_user)
        content = _query_check(minput, variables={'id': region.id}, okay=False)

        # with normal user
        self.force_login(self.project_member_user)
        content = _query_check(minput, variables={'id': self.region.id})['data']['updateRegion']['result']
        self.assertEqual(content['title'], minput['title'], content)

    def test_publish_region(self):
        mutation_query = '''
            mutation MyMutation($id:ID!){
                publishRegion(id: $id) {
                    ok
                    errors
                }
            }
        '''

        def _query_check(**kwargs):
            return self.query_check(
                mutation_query,
                variables={'id': self.region.id},
                **kwargs
            )

        # without login user
        _query_check(assert_for_error=True)

        # login with other user
        self.force_login(self.non_project_member_user)
        content = _query_check()
        self.assertEqual(
            content['data']['publishRegion']['errors'][0]['messages'],
            ['Authorized User can only published the region']
        )

        # login with user
        self.force_login(self.project_member_user)
        content = _query_check()
        self.region.refresh_from_db()
        self.assertEqual(content['data']['publishRegion']['errors'], None)
        self.assertEqual(self.region.is_published, True)
