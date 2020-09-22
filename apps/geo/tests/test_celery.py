from django.test import TestCase, override_settings
from geo.tasks import add


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class CeleryTest(TestCase):
    """
    Simple celery test
    """

    def test_add(self):
        """
        Test the addition task
        """

        result = add.delay(5, 4)
        self.assertEqual(result.get(), 9)
        self.assertTrue(result.successful())
