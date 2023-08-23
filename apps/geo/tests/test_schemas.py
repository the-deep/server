from utils.graphene.tests import GraphQLTestCase

from geo.models import AdminLevel

from project.factories import ProjectFactory
from user.factories import UserFactory
from geo.factories import RegionFactory, AdminLevelFactory, GeoAreaFactory


class TestGeoSchema(GraphQLTestCase):
    GEO_QUERY = '''
        query GeoQuery(
            $projectId: ID!,
            $adminLevelIds: [ID!],
            $regionIds: [ID!],
            $search: String
        ) {
          project(id: $projectId) {
            geoAreas(
                ordering: ASC_ID,
                adminLevelIds: $adminLevelIds,
                regionIds: $regionIds,
                search: $search
            ) {
              page
              pageSize
              totalCount
              results {
                id
                regionTitle
                adminLevelLevel
                adminLevelTitle
                title
                parentTitles
              }
            }
          }
        }
    '''

    def test_geo_filters(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        project.add_member(user)
        region1, region2, region3 = RegionFactory.create_batch(3, is_published=True)
        region4 = RegionFactory.create(is_published=False)

        project.regions.set([region1, region2, region4])

        # Admin level
        region_1_admin_level_1 = AdminLevelFactory.create(region=region1)
        region_1_admin_level_2 = AdminLevelFactory.create(region=region1)
        region_2_admin_level_1 = AdminLevelFactory.create(region=region2)
        region_3_admin_level_0 = AdminLevelFactory.create(region=region3)
        region_4_admin_level_0 = AdminLevelFactory.create(region=region4)
        # Geo areas
        region_1_ad_1_geo_areas = GeoAreaFactory.create_batch(3, admin_level=region_1_admin_level_1)
        region_1_ad_2_geo_areas = GeoAreaFactory.create_batch(
            5,
            admin_level=region_1_admin_level_2,
            title='XYZ Geô'
        )
        region_2_ad_1_geo_areas = GeoAreaFactory.create_batch(4, admin_level=region_2_admin_level_1)
        GeoAreaFactory.create_batch(2, admin_level=region_3_admin_level_0)
        GeoAreaFactory.create_batch(4, admin_level=region_4_admin_level_0)

        def _query_check(filters, **kwargs):
            return self.query_check(
                self.GEO_QUERY,
                variables={
                    **filters,
                    'projectId': str(project.id),
                },
                **kwargs,
            )

        # Without authentication -----
        content = _query_check({}, assert_for_error=True)

        # With authentication -----
        self.force_login(user)

        # With filters
        for name, filters, geo_areas in (
            (
                'no-filter',
                dict(),
                [*region_1_ad_1_geo_areas, *region_1_ad_2_geo_areas, *region_2_ad_1_geo_areas]
            ),
            ('invalid-region-id', dict(regionIds=[str(region3.pk)]), []),
            (
                'valid-region-id',
                dict(regionIds=[str(region1.pk)]),
                [*region_1_ad_1_geo_areas, *region_1_ad_2_geo_areas]
            ),
            ('invalid-admin-level-id', dict(adminLevelIds=[str(region_3_admin_level_0.pk)]), []),
            (
                'valid-admin-level-id',
                dict(adminLevelIds=[str(region_1_admin_level_1.pk)]),
                region_1_ad_1_geo_areas,
            ),
            ('search', dict(search='XYZ Geo'), region_1_ad_2_geo_areas),
        ):
            content = _query_check(filters)['data']['project']['geoAreas']
            self.assertEqual(content['totalCount'], len(geo_areas), (name, content))
            self.assertEqual(len(content['results']), len(geo_areas), (name, content))
            self.assertListIds(content['results'], geo_areas, (name, content))

    def test_geo_query(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        project.add_member(user)
        region1, region2 = RegionFactory.create_batch(2, is_published=True)
        region3 = RegionFactory.create(is_published=False)

        project.regions.set([region1, region2, region3])

        # Admin level
        region_1_admin_level_1 = AdminLevelFactory.create(region=region1, level=1)
        region_1_admin_level_2 = AdminLevelFactory.create(region=region1, level=2)
        region_1_admin_level_3 = AdminLevelFactory.create(region=region1, level=3)
        region_2_admin_level_1 = AdminLevelFactory.create(region=region2, level=1)
        region_2_admin_level_2 = AdminLevelFactory.create(region=region2, level=2)
        region_2_admin_level_3 = AdminLevelFactory.create(region=region2, level=3)
        region_3_admin_level_1 = AdminLevelFactory.create(region=region3, level=1)
        # Geo areas
        # -- Root nodes
        region_1_ad_1_geo_area_01 = GeoAreaFactory.create(admin_level=region_1_admin_level_1)
        GeoAreaFactory.create(admin_level=region_2_admin_level_1)
        region_3_ad_1_geo_area_01 = GeoAreaFactory.create(admin_level=region_3_admin_level_1)
        # -- Sub nodes
        region_1_ad_2_geo_area_01 = GeoAreaFactory.create(
            title='child (Region 1, AdminLevel 2) Geo Area 01',
            admin_level=region_1_admin_level_2,
            parent=region_1_ad_1_geo_area_01,
        )
        region_1_ad_2_geo_area_02 = GeoAreaFactory.create(
            title='child (Region 1, AdminLevel 2) Geo Area 02',
            admin_level=region_1_admin_level_2,
            parent=region_1_ad_1_geo_area_01,
        )
        region_1_ad_2_geo_area_03 = GeoAreaFactory.create(
            title='child (Region 1, AdminLevel 2) Geo Area 03',
            admin_level=region_1_admin_level_2
        )
        region_2_ad_2_geo_area_01 = GeoAreaFactory.create(admin_level=region_2_admin_level_2)
        GeoAreaFactory.create(
            title='child (Region 3, AdminLevel 2) Geo Area 01',
            admin_level=region_3_admin_level_1,
            parent=region_3_ad_1_geo_area_01,
        )
        # -- Sub Sub nodes
        region_1_ad_3_geo_area_01 = GeoAreaFactory.create(
            title='child (Region 1, AdminLevel 3) Geo Area 01',
            admin_level=region_1_admin_level_3,
            parent=region_1_ad_2_geo_area_01,
        )
        region_2_ad_2_geo_area_01 = GeoAreaFactory.create(
            title='child (Region 1, AdminLevel 3) Geo Area 01',
            admin_level=region_2_admin_level_3,
        )

        def _query_check(**kwargs):
            return self.query_check(
                self.GEO_QUERY,
                variables={
                    'projectId': str(project.id),
                    'search': 'child',
                },
                **kwargs,
            )

        # With authentication -----
        self.force_login(user)

        for admin_level in AdminLevel.objects.all():
            admin_level.calc_cache()

        content = _query_check()['data']['project']['geoAreas']
        self.assertEqual(content['results'], [
            {
                'id': str(geo_area.id),
                'title': geo_area.title,
                'adminLevelLevel': geo_area.admin_level.level,
                'adminLevelTitle': geo_area.admin_level.title,
                'regionTitle': geo_area.admin_level.region.title,
                'parentTitles': [
                    parent.title
                    for parent in parents
                ],
            }
            for geo_area, parents in [
                (region_1_ad_2_geo_area_01, [region_1_ad_1_geo_area_01]),
                (region_1_ad_2_geo_area_02, [region_1_ad_1_geo_area_01]),
                (region_1_ad_2_geo_area_03, []),
                (region_1_ad_3_geo_area_01, [region_1_ad_1_geo_area_01, region_1_ad_2_geo_area_01]),
                (region_2_ad_2_geo_area_01, [])
            ]
        ])
