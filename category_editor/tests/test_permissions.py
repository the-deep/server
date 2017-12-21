from rest_framework import status
from rest_framework.test import APITestCase
from user.tests.test_apis import AuthMixin
from category_editor.tests.test_apis import CategoryEditorMixin
from project.tests.test_apis import ProjectMixin
from project.models import ProjectMembership


class CategoryEditorPermissionsTest(
        AuthMixin,
        CategoryEditorMixin,
        ProjectMixin,
        APITestCase):
    """
    Permisssion tests for category editor api
    """
    def setUp(self):
        self.auth = self.get_auth()

        # Create a project, an category editor and a new test user
        category_editor = self.create_or_get_category_editor()
        test_user = self.create_new_user()
        project = self.create_or_get_project()

        project.category_editor = category_editor
        project.save()

        # Change admin to new test user
        ProjectMembership.objects.filter(
            project=category_editor.project_set.first()
        ).delete()

        ProjectMembership.objects.create(
            project=category_editor.project_set.first(),
            member=test_user,
        )

        # The url and data used for requests
        self.url = '/api/v1/category-editors/{}/'.format(
            category_editor.id
        )
        self.data = {}
        self.category_editor = category_editor

    def get_patch_response(self):
        # Try a patch request
        response = self.client.patch(self.url, self.data,
                                     HTTP_AUTHORIZATION=self.auth,
                                     format='json')
        return response

    def test_404(self):
        """
        Test whether a non-project member can access the category editor
        """
        self.assertEqual(self.get_patch_response().status_code,
                         status.HTTP_404_NOT_FOUND)

    # There's no need for any more tests since all other cases
    # are successful ones and are auto tested when testing the
    # respective apis.
