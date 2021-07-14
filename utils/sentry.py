import os

import logging
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

# Celery Terminated Exception: The worker processing a job has been terminated by user request.
from billiard.exceptions import Terminated
logger = logging.getLogger(__name__)

IGNORED_ERRORS = [Terminated, 'graphql.execution.utils']


class InvalidGitRepository(Exception):
    pass


def fetch_git_sha(path, head=None):
    """
    Source: https://github.com/getsentry/raven-python/blob/03559bb05fd963e2be96372ae89fb0bce751d26d/raven/versioning.py
    >>> fetch_git_sha(os.path.dirname(__file__))
    """
    if not head:
        head_path = os.path.join(path, '.git', 'HEAD')
        if not os.path.exists(head_path):
            raise InvalidGitRepository(
                'Cannot identify HEAD for git repository at %s' % (path,))

        with open(head_path, 'r') as fp:
            head = str(fp.read()).strip()

        if head.startswith('ref: '):
            head = head[5:]
            revision_file = os.path.join(
                path, '.git', *head.split('/')
            )
        else:
            return head
    else:
        revision_file = os.path.join(path, '.git', 'refs', 'heads', head)

    if not os.path.exists(revision_file):
        if not os.path.exists(os.path.join(path, '.git')):
            raise InvalidGitRepository(
                '%s does not seem to be the root of a git repository' % (path,))

        # Check for our .git/packed-refs' file since a `git gc` may have run
        # https://git-scm.com/book/en/v2/Git-Internals-Maintenance-and-Data-Recovery
        packed_file = os.path.join(path, '.git', 'packed-refs')
        if os.path.exists(packed_file):
            with open(packed_file) as fh:
                for line in fh:
                    line = line.rstrip()
                    if line and line[:1] not in ('#', '^'):
                        try:
                            revision, ref = line.split(' ', 1)
                        except ValueError:
                            continue
                        if ref == head:
                            return str(revision)

        raise InvalidGitRepository(
            'Unable to find ref to head "%s" in repository' % (head,))

    with open(revision_file) as fh:
        return str(fh.read()).strip()


def init_sentry(app_type, tags={}, **config):
    integrations = [
        CeleryIntegration(),
        DjangoIntegration(),
        RedisIntegration(),

    ]
    sentry_sdk.init(
        **config,
        ignore_errors=IGNORED_ERRORS,
        integrations=integrations,
    )
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag('app_type', app_type)
        for tag, value in tags.items():
            scope.set_tag(tag, value)


class SentryGrapheneMiddleware(object):
    """
    Properly capture errors during query execution and send them to Sentry.
    Then raise the error again and let Graphene handle it.
    https://medium.com/open-graphql/monitoring-graphene-django-python-graphql-api-using-sentry-c0b0c07a344f
    """
    # TODO: This need further work (Use this in GraphqlView instead of middleware)

    def on_error(self, root, info, **args):
        def _on_error(error):
            with sentry_sdk.configure_scope() as scope:
                user = info.context.user
                if user and user.id:
                    scope.user = {
                        'id': user.id,
                        'email': user.email,
                    }
                    scope.set_extra('is_superuser', user.is_superuser)
                scope.set_tag('kind', info.operation.operation)
            sentry_sdk.capture_exception(error)
            # log to console
            logger.error(error, exc_info=True)
            raise error
        return _on_error

    def resolve(self, next, root, info, **args):
        return next(root, info, **args).catch(self.on_error(root, info, **args))
