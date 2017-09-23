from django.test import TestCase
from geo.tasks import add


class CeleryTest(TestCase):
    """
    Simple celery test
    """

    def test_add(self):
        """
        Test the addition task
        """

        result = add.delay(5, 4)
        self.assertEquals(result.get(), 9)
        self.assertTrue(result.successful())
