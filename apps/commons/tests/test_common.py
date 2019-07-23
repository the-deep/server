from django.conf import settings
from deep.tests import TestCase


class TestNotificationAPIs(TestCase):

    def test_detect_testmode(self):
        assert settings.TESTING is True
