from os.path import join

from rest_framework import status
from rest_framework.test import APITestCase
from django.conf import settings

from user.tests.auth_mixin import AuthMixin
from geo.models import Region, AdminLevel


class RegionMixin():
    """
    Create or get region mixin
    """
    def create_or_get_region(self, auth, data=None):
        region = Region.objects.all().first()
        if not region:
            url = '/api/v1/regions/'
            data = {
                'code': 'NLP',
                'title': 'Nepal',
                'data': {'testfield': 'testfile'},
                'is_global': True,
            } if data is None else data

            response = self.client.post(url, data,
                                        HTTP_AUTHORIZATION=auth,
                                        format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Region.objects.count(), 1)
            self.assertEqual(response.data['code'], data['code'])
            region = Region.objects.all().first()
        return region


class RegionTests(AuthMixin, RegionMixin, APITestCase):
    """
    Region Tests
    """
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

    def test_create_and_update_region(self):
        """
        Create Or Update Region Test
        """
        self.create_or_get_region(self.auth)


class AdminLevelTests(AuthMixin, RegionMixin, APITestCase):
    """
    Admin Level Tests
    """
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

    def create_or_get_admin_level(self):
        """
        Create Or Update Admin Level
        """
        admin_level = AdminLevel.objects.all().first()
        if not admin_level:
            url = '/api/v1/admin-levels/'
            data = {
                'region': self.create_or_get_region(self.auth).pk,
                'title': 'test',
                'name_prop': 'test',
                'pcode_prop': 'test',
                'parent_name_prop': 'test',
                'parent_pcode_prop': 'test',
            }

            response = self.client.post(url, data,
                                        HTTP_AUTHORIZATION=self.auth,
                                        format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(AdminLevel.objects.count(), 1)
            self.assertEqual(response.data['title'], data['title'])
            admin_level = AdminLevel.objects.all().first()
        return admin_level

    def test_create_and_update_admin_level(self):
        """
        Create Or Update Admin Level Test
        """
        self.create_or_get_admin_level()

    def test_upload_admin_level(self):
        """
        Upload Admin Level GeoShape Test
        """
        admin_level = self.create_or_get_admin_level()
        url = '/api/v1/admin-levels-upload/' + str(admin_level.pk) + '/'
        with open(join(settings.TEST_DIR, 'geo.json'),
                  'rb') as fp:
            data = {
                'geo_shape': fp,
            }

            response = self.client.put(url, data,
                                       HTTP_AUTHORIZATION=self.auth,
                                       format='multipart')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
