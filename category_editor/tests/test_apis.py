from rest_framework.test import APITestCase
from rest_framework import status
from user.tests.test_apis import AuthMixin
from category_editor.models import CategoryEditor
from project.models import Project
from project.tests.test_apis import ProjectMixin


class CategoryEditorMixin():
    """
    Category Editor Mixin
    """
    def create_or_get_category_editor(self):
        """
        Create or get CategoryEditor
        """
        category_editor = CategoryEditor.objects.first()
        if not category_editor:
            category_editor = CategoryEditor.objects.create(
                created_by=self.user,
            )
        return category_editor


class CategoryEditorTests(AuthMixin, ProjectMixin,
                          APITestCase):
    """
    Category Editor Tests
    """
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

    def test_create_category_editor(self):
        """
        Create Category Editor Test
        """
        project = self.create_or_get_project()

        old_count = CategoryEditor.objects.count()
        url = '/api/v1/category-editors/'
        data = {
            'project': project.id,
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CategoryEditor.objects.count(), old_count + 1)

        project = Project.objects.get(id=project.id)
        self.assertEqual(project.category_editor.id, response.data['id'])
