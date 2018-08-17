from deep.tests import TestCase
from category_editor.models import CategoryEditor
from project.models import Project


class CategoryEditorTests(TestCase):
    def test_create_category_editor(self):
        project = self.create(Project, role=self.admin_role)

        ce_count = CategoryEditor.objects.count()
        url = '/api/v1/category-editors/'
        data = {
            'title': 'New Category Editor',
            'project': project.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(CategoryEditor.objects.count(), ce_count + 1)
        project = Project.objects.get(id=project.id)
        self.assertEqual(project.category_editor.id, response.data['id'])

    def test_clone_category_editor(self):
        category_editor = self.create(CategoryEditor)
        project = self.create(
            Project, category_editor=category_editor,
            role=self.admin_role
        )

        url = '/api/v1/clone-category-editor/{}/'.format(category_editor.id)
        data = {
            'project': project.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertNotEqual(response.data['id'], category_editor.id)
        self.assertEqual(response.data['title'],
                         category_editor.title + ' (cloned)')

        project = Project.objects.get(id=project.id)
        self.assertNotEqual(project.category_editor.id,
                            category_editor.id)

        self.assertEqual(project.category_editor.id, response.data['id'])

    def test_classify(self):
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

        category_editor = self.create(CategoryEditor, data=ce_data)
        project = self.create(
            Project, category_editor=category_editor,
            role=self.admin_role)

        text = 'My water aaloooo'
        url = '/api/v1/projects/{}/category-editor/classify/'.format(
            project.id
        )
        data = {
            'text': text,
            'category': 'sector',
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_200(response)

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
