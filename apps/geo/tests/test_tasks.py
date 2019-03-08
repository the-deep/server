from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from deep.tests import TestCase
from geo.tasks import load_geo_areas
from geo.models import Region, AdminLevel, GeoArea
from gallery.models import File

import os


class LoadGeoAreasTaskTest(TestCase):
    def setUp(self):
        super().setUp()

        # Create a dummy region
        region = Region(code='NPL', title='Nepal')
        region.save()

        # Load a shape file from a test shape file and create admin level 0
        admin_level0 = AdminLevel(region=region, parent=None,
                                  title='Zone',
                                  name_prop='ZONE_NAME',
                                  code_prop='HRPCode')
        shape_data = open(
            os.path.join(settings.TEST_DIR,
                         'nepal-geo-json/admin_level2.geo.json'),
            'rb',
        ).read()
        admin_level0.geo_shape_file = File.objects.create(
            title='al2',
            file=SimpleUploadedFile(
                name='al2.geo.json',
                content=shape_data,
            )
        )
        admin_level0.save()

        # Load admin level 1 similarly
        admin_level1 = AdminLevel(region=region, parent=None,
                                  title='District',
                                  name_prop='DISTRICT',
                                  code_prop='HRPCode',
                                  parent_name_prop='ZONE',
                                  parent_code_prop='HRParent')
        shape_data = open(
            os.path.join(settings.TEST_DIR,
                         'nepal-geo-json/admin_level3.geo.json'),
            'rb',
        ).read()
        admin_level1.geo_shape_file = File.objects.create(
            title='al3',
            file=SimpleUploadedFile(
                name='al3.geo.json',
                content=shape_data,
            )
        )
        admin_level1.parent = admin_level0

        admin_level1.save()

        self.region = region
        self.admin_level0 = admin_level0
        self.admin_level1 = admin_level1

    def tearDown(self):
        if os.path.isfile(self.admin_level0.geo_shape_file.file.path):
            os.unlink(self.admin_level0.geo_shape_file.file.path)
        if os.path.isfile(self.admin_level1.geo_shape_file.file.path):
            os.unlink(self.admin_level1.geo_shape_file.file.path)

    def test_load_areas(self):
        result = load_geo_areas(self.region.pk)
        self.assertTrue(result)

        latest_a0 = AdminLevel.objects.get(pk=self.admin_level0.pk)
        latest_a1 = AdminLevel.objects.get(pk=self.admin_level1.pk)
        self.assertFalse(latest_a0.stale_geo_areas)
        self.assertFalse(latest_a1.stale_geo_areas)

        # Test if a geo area in admin level 0 is correctly set
        bagmati = GeoArea.objects.filter(
            title='Bagmati',
            admin_level=self.admin_level0,
            parent=None,
            code='NP-C-BAG',
        ).first()

        self.assertIsNotNone(bagmati)

        # Test if a geo area in admin level 1 is correctly set
        sindhupalchowk = GeoArea.objects.filter(
            title='Sindhupalchok',
            admin_level=self.admin_level1,
            parent__title='Bagmati',
            parent__code='NP-C-BAG',
            code='NP-C-BAG-23',
        ).first()

        self.assertIsNotNone(sindhupalchowk)

    def test_geojson_api(self):
        result = load_geo_areas(self.region.pk)
        self.assertTrue(result)

        # Test if geojson api works
        url = '/api/v1/admin-levels/{}/geojson/'.format(self.admin_level0.pk)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['type'], 'FeatureCollection')
        self.assertIsNotNone(response.data['features'])
        self.assertTrue(len(response.data['features']) > 0)

        # Test if geobounds also works
        url = '/api/v1/admin-levels/{}/geojson/bounds/'.format(
            self.admin_level0.pk
        )

        response = self.client.get(url)
        self.assert_200(response)

        self.assertIsNotNone(response.data['bounds'])
