from django import test
from django.core.management.base import BaseCommand

import cProfile
import pstats
import os


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # test.utils.setup_test_environment()
        # old_config = test.utils.setup_databases(3, False)

        pr = cProfile.Profile()
        pr.enable()
        client = test.Client()
        client.get('/api/v1/users/')
        pr.disable()

        regex = os.getcwd()

        stats = pstats.Stats(pr)
        stats.sort_stats('cumulative')

        print('Stats')
        stats.print_stats(regex)

        print('Callers')
        stats.print_callers(regex)

        print('Callees')
        stats.print_callees(regex)

        print('End')
        # test.utils.teardown_databases(old_config, 3)
        # test.utils.teardown_test_environment()
