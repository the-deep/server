from deep.tests import TestCase
from analysis_framework.models import AnalysisFramework
from project.models import Project


class AnalysisFrameworkTests(TestCase):
    def test_create_analysis_framework(self):
        project = self.create(Project, role=self.admin_role)

        af_count = AnalysisFramework.objects.count()
        url = '/api/v1/analysis-frameworks/'
        data = {
            'title': 'Test AnalysisFramework Title',
            'project': project.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(AnalysisFramework.objects.count(), af_count + 1)
        self.assertEqual(response.data['title'], data['title'])

        project = Project.objects.get(id=project.id)
        self.assertEqual(project.analysis_framework.id, response.data['id'])

    def test_cant_create_private_framework_for_public_project(self):
        project = self.create(Project, role=self.admin_role)

        af_count = AnalysisFramework.objects.count()
        url = '/api/v1/analysis-frameworks/'
        data = {
            'title': 'Private Framework',
            'project': project.id,
            'is_private': True
        }

        self.authenticate()
        response = self.client.post(url, data)

        # Can't create private framework for public
        # project
        self.assert_400(response)

        self.assertEqual(AnalysisFramework.objects.count(), af_count + 1)
        self.assertEqual(response.data['title'], data['title'])
        self.assertEqual(response.data['is_private'], data['is_private'])

        project = Project.objects.get(id=project.id)
        self.assertEqual(project.analysis_framework.id, response.data['id'])

    def test_create_private_framework_for_private_project(self):
        project = self.create(Project, role=self.admin_role, is_private=True)

        af_count = AnalysisFramework.objects.count()
        url = '/api/v1/analysis-frameworks/'
        data = {
            'title': 'Private Framework',
            'project': project.id,
            'is_private': True
        }

        self.authenticate()
        response = self.client.post(url, data)

        self.assert_201(response)

        self.assertEqual(AnalysisFramework.objects.count(), af_count + 1)
        self.assertEqual(response.data['title'], data['title'])
        self.assertEqual(response.data['is_private'], data['is_private'])

        project = Project.objects.get(id=project.id)
        self.assertEqual(project.analysis_framework.id, response.data['id'])

    def test_clone_analysis_framework(self):
        analysis_framework = self.create(AnalysisFramework)
        project = self.create(
            Project, analysis_framework=analysis_framework,
            role=self.admin_role
        )

        url = '/api/v1/clone-analysis-framework/{}/'.format(
            analysis_framework.id
        )
        data = {
            'project': project.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertNotEqual(response.data['id'], analysis_framework.id)
        self.assertEqual(
            response.data['title'],
            analysis_framework.title[:230] + ' (cloned)')

        project = Project.objects.get(id=project.id)
        self.assertNotEqual(project.analysis_framework.id,
                            analysis_framework.id)

        self.assertEqual(project.analysis_framework.id, response.data['id'])

    def test_project_analysis_framework(self):
        analysis_framework = self.create(AnalysisFramework)
        project = self.create(
            Project, analysis_framework=analysis_framework,
            role=self.admin_role
        )

        url = '/api/v1/projects/{}/analysis-framework/'.format(
            project.id
        )

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['id'], analysis_framework.id)
        self.assertEqual(response.data['title'], analysis_framework.title)

    def test_filter_analysis_framework(self):
        url = '/api/v1/analysis-frameworks/'
        self.authenticate()
        response = self.client.get(f'{url}?activity=active&relatedToMe=True')
        self.assert_200(response)
