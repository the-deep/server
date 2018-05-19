from deep.tests import TestCase
from geo.models import Region, AdminLevel, GeoArea
from project.models import Project


class RegionTests(TestCase):
    def test_create_region(self):
        region_count = Region.objects.count()

        project = self.create(Project)
        url = '/api/v1/regions/'
        data = {
            'code': 'NLP',
            'title': 'Nepal',
            'data': {'testfield': 'testfile'},
            'public': True,
            'project': project.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Region.objects.count(), region_count + 1)
        self.assertEqual(response.data['code'], data['code'])
        self.assertIn(Region.objects.get(id=response.data['id']),
                      project.regions.all())

    def test_clone_region(self):
        project = self.create(Project)
        region = self.create(Region)
        project.regions.add(region)

        url = '/api/v1/clone-region/{}/'.format(region.id)
        data = {
            'project': project.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertNotEqual(response.data['id'], region.id)
        self.assertFalse(response.data['public'])
        self.assertFalse(region in project.regions.all())

        new_region = Region.objects.get(id=response.data['id'])
        self.assertTrue(new_region in project.regions.all())

    def test_trigger_api(self):
        region = self.create(Region)
        url = '/api/v1/geo-areas-load-trigger/{}/'.format(region.id)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)


class AdminLevelTests(TestCase):
    def test_create_admin_level(self):
        admin_level_count = AdminLevel.objects.count()

        region = self.create(Region)
        url = '/api/v1/admin-levels/'
        data = {
            'region': region.pk,
            'title': 'test',
            'name_prop': 'test',
            'pcode_prop': 'test',
            'parent_name_prop': 'test',
            'parent_pcode_prop': 'test',
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(AdminLevel.objects.count(), admin_level_count + 1)
        self.assertEqual(response.data['title'], data['title'])


class GeoOptionsApi(TestCase):
    def test_geo_options(self):
        region = self.create(Region)

        admin_level1 = self.create(AdminLevel, region=region)
        admin_level2 = self.create(AdminLevel, region=region)
        geo_area1 = self.create(GeoArea, admin_level=admin_level1)
        geo_area2 = self.create(GeoArea, admin_level=admin_level2,
                                parent=geo_area1)

        url = '/api/v1/geo-options/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data[str(region.id)][1].get('label'),
                         '{} / {}'.format(admin_level2.title,
                                          geo_area2.title))
