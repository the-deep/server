from deep.tests import TestCase
from analysis_framework.models import (
    AnalysisFramework,
    AnalysisFrameworkRole,
    AnalysisFrameworkMembership,
)
from project.models import Project


class AnalysisFrameworkTests(TestCase):

    def test_create_analysis_framework(self):
        project = self.create(Project, role=self.admin_role)

        url = '/api/v1/analysis-frameworks/'
        data = {
            'title': 'Test AnalysisFramework Title',
            'project': project.id,
        }

        response = self.post_and_check_201(url, data, AnalysisFramework, ['title'])

        project = Project.objects.get(id=project.id)
        self.assertEqual(project.analysis_framework.id, response.data['id'])

        # test Group Membership created or not
        assert AnalysisFrameworkMembership.objects.filter(
            framework_id=response.data['id'],
            member=self.user,
            role=project.analysis_framework.get_or_create_owner_role(),
        ).first() is not None, "Membership Should be created"

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
