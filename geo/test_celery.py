from django.test import TestCase
from .tasks import add


class CeleryTest(TestCase):
    def test_add(self):
        result = add.delay(5, 4)
        self.assertEquals(result.get(), 9)
        self.assertTrue(result.successful())
