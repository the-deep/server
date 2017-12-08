from rest_framework.test import APITestCase
from user.tests.test_apis import AuthMixin
from rest_framework import status
from analysis_framework.models import (
    AnalysisFramework, Widget,
    Filter, Exportable
)
from project.models import Project
from project.tests.test_apis import ProjectMixin


# Mixins

class AnalysisFrameworkMixin():
    """
    Analysis Framework Mixin
    """
    def create_or_get_analysis_framework(self):
        """
        Create or get  AnalysisFramework
        """
        analysis_framework = AnalysisFramework.objects.first()
        if not analysis_framework:
            analysis_framework = AnalysisFramework.objects.create(
                title='This is a test AnalysisFramework',
                created_by=self.user,
            )
        return analysis_framework


class WidgetMixin():
    """
    Widget mixin
    """
    def create_or_get_widget(self):
        """
        Create or get widget
        """
        widget = Widget.objects.first()
        if not widget:
            analysis_framework = self.create_or_get_analysis_framework()
            widget = Widget.objects.create(
                analysis_framework=analysis_framework,
                widget_id='TEST_SCHEMA',
                title="Test Title",
            )
        return widget


class FilterMixin():
    """
    Filter mixin
    """
    def create_or_get_filter(self):
        """
        Create or get widget
        """
        filter = Filter.objects.first()
        if not filter:
            analysis_framework = self.create_or_get_analysis_framework()
            filter = Filter.objects.create(
                analysis_framework=analysis_framework,
                widget_id='TEST_SCHEMA',
                title="Test Title"
            )
        return filter


class ExportableMixin():
    """
    Exportable mixin
    """
    def create_or_get_exportable(self):
        """
        Create or get widget
        """
        exportable = Exportable.objects.first()
        if not exportable:
            analysis_framework = self.create_or_get_analysis_framework()
            exportable = Exportable.objects.create(
                analysis_framework=analysis_framework,
                widget_id='TEST_SCHEMA',
            )
        return exportable


# Tests

class AnalysisFrameworkTests(AuthMixin, ProjectMixin,
                             AnalysisFrameworkMixin, APITestCase):
    """
    Analysis Framework Tests
    """
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

    def test_create_analysis_framework(self):
        """
        Create Analysis Framework Test
        """
        old_count = AnalysisFramework.objects.count()
        url = '/api/v1/analysis-frameworks/'
        data = {
            'title': 'Test AnalysisFramework Title',
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AnalysisFramework.objects.count(), old_count + 1)
        self.assertEqual(response.data['title'], data['title'])

    def test_clone_analysis_framework(self):
        """
        Test cloning
        """
        project = self.create_or_get_project()
        analysis_framework = self.create_or_get_analysis_framework()
        project.analysis_framework = analysis_framework
        project.save()

        url = '/api/v1/clone-analysis-framework/{}/'.format(
            analysis_framework.id
        )
        data = {
            'project': project.id,
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data['id'], analysis_framework.id)

        project = Project.objects.get(id=project.id)
        self.assertNotEqual(project.analysis_framework.id,
                            analysis_framework.id)

        new_af = AnalysisFramework.objects.get(id=response.data['id'])
        self.assertEqual(project.analysis_framework.id, new_af.id)


class WidgetTests(AuthMixin, AnalysisFrameworkMixin, APITestCase):
    """
    Widget Tests
    """
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

    def test_create_export_widget(self):
        """
        Create Widget Test
        """
        old_count = Widget.objects.count()
        url = '/api/v1/analysis-framework-widgets/'
        data = {
            'analysis_framework': self.create_or_get_analysis_framework().pk,
            'widget_id': 'TEST_SCHEMA',
            'title': 'Test Title',
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Widget.objects.count(), old_count + 1)
        self.assertEqual(response.data['title'], data['title'])
        self.assertEqual(response.data['widget_id'], data['widget_id'])


class FilterTests(AuthMixin, AnalysisFrameworkMixin, APITestCase):
    """
    Filter Tests
    """
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

    def test_create_export_filter(self):
        """
        Create Filter Test
        """
        # TODO: Add better properties
        old_count = Filter.objects.count()
        url = '/api/v1/analysis-framework-filters/'
        data = {
            'analysis_framework': self.create_or_get_analysis_framework().pk,
            'widget_id': 'TEST_SCHEMA',
            'title': 'Test Title',
            'properties': {},
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Filter.objects.count(), old_count + 1)
        self.assertEqual(response.data['title'], data['title'])
        self.assertEqual(response.data['widget_id'], data['widget_id'])
        self.assertEqual(response.data['properties'], data['properties'])


class ExportableTests(AuthMixin, AnalysisFrameworkMixin, APITestCase):
    """
    Exportable Tests
    """
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

    def test_create_export_exportable(self):
        """
        Create Exportable Test
        """
        old_count = Exportable.objects.count()
        url = '/api/v1/analysis-framework-exportables/'
        data = {
            'analysis_framework': self.create_or_get_analysis_framework().pk,
            'widget_id': 'TEST_SCHEMA',
            'inline': True,
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Exportable.objects.count(), old_count + 1)
        self.assertEqual(response.data['inline'], data['inline'])
        self.assertEqual(response.data['widget_id'], data['widget_id'])
