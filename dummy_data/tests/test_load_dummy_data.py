from django.core.management import call_command
from django.test import TestCase
from io import StringIO


class CommandTestCase(TestCase):
    def test_load_dummy_data(self):
        out = StringIO()
        call_command('load_dummy_data', stdout=out)

        # If any error was raised, the test fails automatically.
        # Just check that we are done.
        self.assertEqual(out.getvalue().strip().split('\n')[-1],
                         'Done')

        # TODO: Check if leads, projects, and so on were added??
