import json

from geo.models import AdminLevel, GeoArea, Region
from project.models import Project

from deep.tests import TestCase


class RegionTests(TestCase):
    def test_create_region(self):
        region_count = Region.objects.count()

        project = self.create(Project, role=self.admin_role)
        url = "/api/v1/regions/"
        data = {
            "code": "NLP",
            "title": "Nepal",
            "data": {"testfield": "testfile"},
            "public": True,
            "project": project.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Region.objects.count(), region_count + 1)
        self.assertEqual(response.data["code"], data["code"])
        self.assertIn(Region.objects.get(id=response.data["id"]), project.regions.all())

    def test_region_published_status(self):
        """
        Once published is set to True for region don't allow it to modify
        """
        project = self.create(Project, role=self.admin_role)
        region = self.create(Region, is_published=True)
        project.regions.add(region)

        data = {"is_published": False}
        url = f"/api/v1/regions/{region.id}/"
        self.authenticate()
        response = self.client.patch(url, data)
        self.assert_403(response)

    def test_publish_region(self):
        user = self.create_user()
        user1 = self.create_user()
        project = self.create(Project, role=self.admin_role)
        region = self.create(Region, created_by=user)
        project.regions.add(region)

        url = f"/api/v1/regions/{region.id}/publish/"
        data = {}

        # authenticated with user that has not created region
        self.authenticate(user1)
        response = self.client.post(url, data)
        self.assert_400(response)

        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_200(response)
        self.assertEqual(response.data["is_published"], True)

    def test_clone_region(self):
        project = self.create(Project, role=self.admin_role)
        region = self.create(Region)
        project.regions.add(region)

        url = "/api/v1/clone-region/{}/".format(region.id)
        data = {
            "project": project.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertNotEqual(response.data["id"], region.id)
        self.assertFalse(response.data["public"])
        self.assertFalse(region in project.regions.all())

        new_region = Region.objects.get(id=response.data["id"])
        self.assertTrue(new_region in project.regions.all())

    def test_region_filter_not_in_project(self):
        project_1 = self.create(Project, role=self.admin_role)
        project_2 = self.create(Project, role=self.admin_role)
        region_1 = self.create(Region)
        region_2 = self.create(Region)
        region_3 = self.create(Region)
        project_1.regions.add(region_1)
        project_1.regions.add(region_2)
        project_2.regions.add(region_3)

        # filter regions in project
        url = f"/api/v1/regions/?project={project_1.id}"
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(set(rg["id"] for rg in response.data["results"]), set([region_1.id, region_2.id]))

        # filter the region that are not in project
        url = f"/api/v1/regions/?exclude_project={project_1.id}"
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], region_3.id)

    def test_trigger_api(self):
        region = self.create(Region)
        url = "/api/v1/geo-areas-load-trigger/{}/".format(region.id)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)


class AdminLevelTests(TestCase):
    def test_create_admin_level(self):
        admin_level_count = AdminLevel.objects.count()

        region = self.create(Region)
        url = "/api/v1/admin-levels/"
        data = {
            "region": region.pk,
            "title": "test",
            "name_prop": "test",
            "pcode_prop": "test",
            "parent_name_prop": "test",
            "parent_pcode_prop": "test",
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(AdminLevel.objects.count(), admin_level_count + 1)
        self.assertEqual(response.data["title"], data["title"])


class GeoOptionsApi(TestCase):
    def test_geo_options(self):
        region1 = self.create(Region, title="Region 1")
        region2 = self.create(Region, title="Region 2")
        region3 = self.create(Region, title="Region 3")

        project = self.create_project()
        project.regions.add(region1, region2)
        admin_level1_1 = self.create(AdminLevel, title="AdminLevel1", region=region1, level=0)
        admin_level1_2 = self.create(AdminLevel, title="AdminLevel2", region=region2, level=1)
        admin_level2_1 = self.create(AdminLevel, title="AdminLevel1", region=region1, level=0)
        self.create(AdminLevel, title="AdminLevel1", region=region2, level=0)
        self.create(AdminLevel, title="AdminLevel2", region=region2, level=1)
        self.create(AdminLevel, title="AdminLevel1", region=region3, level=0)
        self.create(AdminLevel, title="AdminLevel2", region=region3, level=1)
        geo_area1_1 = self.create(GeoArea, title="GeoArea1", admin_level=admin_level1_1)
        geo_area1_2 = self.create(GeoArea, title="GeoArea2", admin_level=admin_level1_2, parent=geo_area1_1)
        self.create(GeoArea, title="GeoArea2", admin_level=admin_level2_1)

        url = f"/api/v1/geo-options/?project={project.pk}"

        self.authenticate()
        response = self.client.get(url, follow=True)
        self.assert_200(response)
        cached_file_url = response.data["geo_options_cached_file"]

        data = json.loads(b"".join(list(self.client.get(cached_file_url).streaming_content)))
        self.assertEqual(data[str(region1.id)][1].get("label"), "{} / {}".format(admin_level1_1.title, geo_area1_2.title))

        # check if parent is present in geo options
        for _, options in data.items():
            for option in options:
                assert "parent" in option

        # URL should be same for future request
        response = self.client.get(url, follow=True)
        self.assert_200(response)
        assert cached_file_url == response.data["geo_options_cached_file"]

        # URL should be changed if region data is changed
        region1.refresh_from_db()
        region1.cache_index += 1
        region1.save(update_fields=("cache_index",))
        response = self.client.get(url, follow=True)
        self.assert_200(response)
        assert cached_file_url != response.data["geo_options_cached_file"]
        cached_file_url = response.data["geo_options_cached_file"]

        # URL should be same again for future request
        response = self.client.get(url, follow=True)
        self.assert_200(response)
        assert cached_file_url == response.data["geo_options_cached_file"]

        # URL shouldn't be changed if non assigned region data is changed
        region3.refresh_from_db()
        region3.cache_index += 1
        region3.save(update_fields=("cache_index",))
        response = self.client.get(url, follow=True)
        self.assert_200(response)
        assert cached_file_url == response.data["geo_options_cached_file"]


class TestGeoAreaApi(TestCase):
    def test_geo_area(self):
        region = self.create(Region, is_published=True)
        region1 = self.create(Region, is_published=False)
        region2 = self.create(Region, is_published=True)
        user1 = self.create_user()
        user2 = self.create_user()
        project = self.create(Project)
        project.add_member(user1)
        project.regions.set([region, region1])
        project2 = self.create(Project)
        project2.add_member(user2)
        project2.regions.add(region2)

        admin_level1 = self.create(AdminLevel, region=region, title="test")
        admin_level2 = self.create(AdminLevel, region=region)
        admin_level3 = self.create(AdminLevel, region=region1)
        admin_level4 = self.create(AdminLevel, region=region2)
        geo_area1 = self.create(GeoArea, admin_level=admin_level1, title="me")
        self.create(GeoArea, admin_level=admin_level2, parent=geo_area1)
        self.create(GeoArea, admin_level=admin_level4)
        self.create(GeoArea, admin_level=admin_level3)

        url = f"/api/v1/projects/{project.id}/geo-area/"

        self.authenticate(user1)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data["count"], 2)  # geo area with region `published=True`
        # test for the label
        self.assertEqual(response.data["results"][0]["label"], "{}/{}".format(admin_level1.title, geo_area1.title))

        # test for the not project member
        self.authenticate(user2)
        response = self.client.get(url)
        self.assert_403(response)

        # test for the pagination
        url = f"/api/v1/projects/{project.id}/geo-area/?limit=1"
        self.authenticate(user1)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data["results"]), 1)

        # test for the search field
        url = f"/api/v1/projects/{project.id}/geo-area/?label=test"
        self.authenticate(user1)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data["count"], 1)

        # Passing the label that is not either region or geoarea title
        url = f"/api/v1/projects/{project.id}/geo-area/?label=acd"
        self.authenticate(user1)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data["count"], 0)
