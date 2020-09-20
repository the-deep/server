import logging
import requests
import threading

from reversion.views import create_revision
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import get_storage_class

from utils.date_extractor import str_to_date

logger = logging.getLogger(__name__)


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


_threadlocal = threading.local()


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
