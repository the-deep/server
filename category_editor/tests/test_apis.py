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
                title='Test Category Editor',
                created_by=self.user,
            )
        return category_editor


class CategoryEditorTests(AuthMixin, ProjectMixin, CategoryEditorMixin,
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
            'title': 'New Category Editor',
            'project': project.id,
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CategoryEditor.objects.count(), old_count + 1)

        project = Project.objects.get(id=project.id)
        self.assertEqual(project.category_editor.id, response.data['id'])

    def test_clone_category_editor(self):
        """
        Test cloning
        """
        project = self.create_or_get_project()
        category_editor = self.create_or_get_category_editor()
        project.category_editor = category_editor
        project.save()

        url = '/api/v1/clone-category-editor/{}/'.format(
            category_editor.id
        )
        data = {
            'project': project.id,
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data['id'], category_editor.id)
        self.assertEqual(response.data['title'],
                         category_editor.title + ' (cloned)')

        project = Project.objects.get(id=project.id)
        self.assertNotEqual(project.category_editor.id,
                            category_editor.id)

        self.assertEqual(project.category_editor.id, response.data['id'])

    def test_classify(self):
        """
        First create a dummy category edtior and then test classifying
        text with it
        """

        project = self.create_or_get_project()
        category_editor = self.create_or_get_category_editor()
        project.category_editor = category_editor
        project.save()

        ce_data = {
            'categories': [
                {
                    'title': 'Sector',
                    'subcategories': [
                        {
                            'title': 'WASH',
                            'ngrams': {
                                1: ['affected', 'water'],
                                2: ['affected not', 'water not'],
                            },
                        },
                    ],
                },
            ],
        }
        category_editor.data = ce_data
        category_editor.save()

        text = 'My water aaloooo'

        url = '/api/v1/projects/{}/category-editor/classify/'.format(
            project.id
        )
        data = {
            'text': text,
            'category': 'sector',
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected = [
            {
                'title': 'WASH',
                'keywords': [
                    {'start': 3, 'length': 5, 'subcategory': 'WASH'},
                ],
            },
        ]
        got = [dict(c) for c in response.data.get('classifications')]
        for g in got:
            g['keywords'] = [
                dict(k) for k in g['keywords']
            ]
        self.assertEqual(got, expected)
