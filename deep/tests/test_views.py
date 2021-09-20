import uuid

from django.test import TestCase, Client
from django.urls import reverse

from deep.views import FrontendView
from project.models import ProjectStats
from project.factories import ProjectFactory


class TestIndexView(TestCase):
    def test_index_view(self):
        client = Client()

        response = client.get('/')
        self.assertEqual(response.resolver_match.func.__name__,
                         FrontendView.as_view().__name__)


class ProjectVizView(TestCase):
    def test_x_frame_headers(self):
        client = Client()
        url = reverse('server-frontend')
        response = client.get(url)
        # There should be x-frame-options by default in views
        assert 'X-Frame-Options' in response.headers

        project = ProjectFactory.create()
        stat = ProjectStats.objects.create(project=project, token=uuid.uuid4())
        url = reverse('project-stat-viz-public', kwargs={
            'project_stat_id': stat.id,
            'token': stat.token,
        })
        response = client.get(url)
        # There should not be x-frame-options in specific views like project-stat-viz-public
        assert 'X-Frame-Options' not in response.headers
