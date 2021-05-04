import logging
import requests
import threading

from reversion.views import create_revision
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.utils.translation import gettext
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.files.storage import get_storage_class

from utils.date_extractor import str_to_date

PERMISSION_DENIED_MESSAGE = 'You do not have permission to perform this action.'

logger = logging.getLogger(__name__)
_threadlocal = threading.local()


class RevisionMiddleware:
    skip_paths = [
        '/api/v1/token/',
    ]

    def __init__(self, get_response):
        if get_response is not None:
            self.get_response = create_revision()(get_response)
        self.original_get_response = get_response

    def __call__(self, request):
        if request.path in self.skip_paths:
            return self.original_get_response(request)
        return self.get_response(request)


def get_s3_signed_url_ttl():
    """
    !!! Do not use if your operation is asynchronus !!!
    """
    ttl = getattr(_threadlocal, DeepInnerCacheMiddleware.THREAD_S3_SIGNED_URL_TTL_ATTRIBUTE, None)
    if ttl is None:
        ttl = DeepInnerCacheMiddleware.get_cache_ttl()
        setattr(_threadlocal, DeepInnerCacheMiddleware.THREAD_S3_SIGNED_URL_TTL_ATTRIBUTE, ttl)
    return ttl


class DeepInnerCacheMiddleware:
    EC2_META_URL = 'http://169.254.169.254/latest/meta-data/iam/security-credentials/'
    THREAD_S3_SIGNED_URL_TTL_ATTRIBUTE = 'URLCachedFileField__get_cache_ttl'

    @classmethod
    def get_cache_ttl(cls):
        if getattr(get_storage_class()(), 'access_key', None) is not None:
            return settings.MAX_FILE_CACHE_AGE

        # Assume IAM Role is being used
        try:
            iam_role_resp = requests.get(cls.EC2_META_URL, timeout=0.01)
            if iam_role_resp.status_code == 200:
                expiration = str_to_date(
                    requests.get(cls.EC2_META_URL + iam_role_resp.text, timeout=0.01).json()['Expiration']
                )
                return max(0, expiration.timestamp() - timezone.now().timestamp())
        except requests.exceptions.RequestException:
            logger.error('Failed to retrive IAM Role session expiration.', exc_info=True)
        # Avoid cache for now (This shouldn't happen)
        return 0

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_function, *args, **kwargs):
        setattr(_threadlocal, self.THREAD_S3_SIGNED_URL_TTL_ATTRIBUTE, None)


def _do_set_current_request(request_fun):
    setattr(_threadlocal, 'request', request_fun.__get__(request_fun, threading.local))


def _set_current_request(request=None):
    '''
    Sets current user in local thread.
    Can be used as a hook e.g. for shell jobs (when request object is not
    available).
    '''
    _do_set_current_request(lambda self: request)


class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        _do_set_current_request(lambda self: request)
        return self.get_response(request)


def get_current_request():
    """
    !!! Do not use if your operation is asynchronus !!!
    Allow to access current request in signals
    This is a hack that looks into the thread
    Mainly used for log purpose
    """

    request = getattr(_threadlocal, "request", None)
    if callable(request):
        return request()
    return request


def get_current_user():
    request = get_current_request()
    current_user = request and request.user
    if isinstance(current_user, AnonymousUser):
        return None
    return current_user


class WhiteListMiddleware:
    '''
    Graphql node whitelist for unauthenticated user
    '''
    def resolve(self, next, root, info, **args):
        # if user is not authenticated and user is not accessing
        # whitelisted nodes, then raise permission denied error

        # furthermore, this check must only happen in the root node, and not in deeper nodes
        if not hasattr(self, '_skip_white_list_check'):
            if not info.context.user.is_authenticated and info.field_name not in settings.GRAPHENE_NODES_WHITELIST:
                raise PermissionDenied(gettext(PERMISSION_DENIED_MESSAGE))
        self._skip_white_list_check = True
        return next(root, info, **args)


class DisableIntrospectionSchemaMiddleware:
    """
    This middleware should be used in production.
    """
    def resolve(self, next, root, info, **args):
        if info.field_name == '__schema':
            return None
        return next(root, info, **args)
