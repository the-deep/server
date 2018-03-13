from django import test
from django.conf import settings

import cProfile
import pstats
import os

from jwt_auth.token import AccessToken


TEST_SETUP_VERBOSITY = 1


class Profiler:
    def __init__(self):
        self.created = False
        self.pr = None
        self.create()

    def __enter__(self):
        if not self.created:
            self.create()
        return self

    def create(self):
        self.last_test_settings = settings.TESTING
        settings.TESTING = True
        test.utils.setup_test_environment()
        self.old_config = test.utils.setup_databases(
            TEST_SETUP_VERBOSITY,
            False,
        )
        self.client = test.Client()
        self.client.get('/')

        self.created = True

    def __exit__(self, exc_type, exc_value, traceback):
        if self.created:
            self.destroy()

    def __del__(self):
        if self.created:
            self.destroy()

    def destroy(self):
        if self.pr:
            self.pr.disable()
            self.print_stats()
        settings.TESTING = self.last_test_settings
        test.utils.teardown_databases(self.old_config, TEST_SETUP_VERBOSITY)
        test.utils.teardown_test_environment()
        self.created = False

    def authorise_with(self, user):
        self.access = AccessToken.for_user(user).encode()
        self.auth = 'Bearer {0}'.format(self.access)

    def start_profiling(self):
        self.pr = cProfile.Profile(builtins=False)
        self.pr.enable()

    def stop_profiling(self):
        if not self.pr:
            return

        self.pr.disable()
        self.stats = pstats.Stats(self.pr)
        self.stats.sort_stats('cumulative')
        self.pr = None

    def print_stats(self):
        regex = '({})|(\/db\/models.*(fetch|execute_sql))'\
            .format(os.getcwd())

        print('Stats')
        self.stats.print_stats(regex)

        # print('Callers')
        # self.stats.print_callers(regex)

        # print('Callees')
        # self.stats.print_callees(regex)

        print('End')

    def profile_get(self, *args, **kwargs):
        self.start_profiling()

        self.client.get(
            HTTP_AUTHORIZATION=self.auth,
            *args,
            **kwargs,
        )

        self.stop_profiling()

        # print('Response:')
        # print(r.data)
        # print('\n\n')
        self.print_stats()

    def profile_post(self, *args, **kwargs):
        self.start_profiling()

        self.client.post(
            HTTP_AUTHORIZATION=self.auth,
            *args,
            **kwargs,
        )

        self.stop_profiling()

        # print('Response:')
        # print(r.data)
        # print('\n\n')
        self.print_stats()

    def profile_patch(self, *args, **kwargs):
        self.start_profiling()

        self.client.patch(
            HTTP_AUTHORIZATION=self.auth,
            *args,
            **kwargs,
        )

        self.stop_profiling()

        # print('Response:')
        # print(r.data)
        # print('\n\n')
        self.print_stats()
