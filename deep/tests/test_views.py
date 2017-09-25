from django.test import TestCase, Client
from deep.views import FrontendView


class TestIndexView(TestCase):
    def test_index_view(self):
        client = Client()

        response = client.get('/')
        self.assertEqual(response.resolver_match.func.__name__,
                         FrontendView.as_view().__name__)
