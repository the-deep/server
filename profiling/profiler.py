from django import test
from django.conf import settings

import cProfile
import pstats
import os

from jwt_auth.token import AccessToken


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
        self.old_config = test.utils.setup_databases(3, False)
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
        test.utils.teardown_databases(self.old_config, 3)
        test.utils.teardown_test_environment()
        self.created = False

    def authorise_with(self, user):
        self.access = AccessToken.for_user(user).encode()
        self.auth = 'Bearer {0}'.format(self.access)

    def start_profiling(self):
        self.pr = cProfile.Profile()
        self.pr.enable()

    def stop_profiling(self):
        self.pr.disable()
        self.print_stats()
        self.pr = None

    def print_stats(self):
        if not self.pr:
            return

        regex = os.getcwd()
        stats = pstats.Stats(self.pr)
        stats.sort_stats('cumulative')

        print('Stats')
        stats.print_stats(regex)

        print('Callers')
        stats.print_callers(regex)

        print('Callees')
        stats.print_callees(regex)

        print('End')

    def profile_get(self, *args, **kwargs):
        self.start_profiling()

        r = self.client.get(
            HTTP_AUTHORIZATION=self.auth,
            *args,
            **kwargs,
        )

        print('Response:')
        print(r.data)
        print('\n\n')

        self.stop_profiling()

    def profile_post(self, *args, **kwargs):
        self.start_profiling()

        r = self.client.post(
            HTTP_AUTHORIZATION=self.auth,
            *args,
            **kwargs,
        )

        print('Response:')
        print(r.data)
        print('\n\n')

        self.stop_profiling()

    def profile_patch(self, *args, **kwargs):
        self.start_profiling()

        r = self.client.patch(
            HTTP_AUTHORIZATION=self.auth,
            *args,
            **kwargs,
        )

        print('Response:')
        print(r.data)
        print('\n\n')

        self.stop_profiling()
