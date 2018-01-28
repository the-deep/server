from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse, unquote
from django.core.management.base import BaseCommand

import requests
import os

from gallery.models import File


class MigrationCommand(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            dest='DEEP_1_URL',
        )
        parser.add_argument(
            '--user',
            dest='DEEP_1_USER',
        )
        parser.add_argument(
            '--password',
            dest='DEEP_1_PASSWORD',
        )
        parser.add_argument(
            '--use_s3',
            dest='DJANGO_USE_S3',
        )

    def handle(self, *args, **kwargs):
        valid_keys = [
            'DEEP_1_URL',
            'DEEP_1_USER',
            'DEEP_1_PASSWORD',
            'DJANGO_USE_S3',
        ]
        for key, value in kwargs.items():
            if key in valid_keys and value:
                os.environ.setdefault(key, value)
        self.run()

    def run(self):
        pass


# BASE_URL = 'http://www.thedeep.io'
# BASE_URL = os.environ.get('DEEP_1_URL', 'http://172.21.0.1:9000')
# USERNAME = os.environ.get('DEEP_1_USER', 'test@toggle.com')
# PASSWORD = os.environ.get('DEEP_1_PASSWORD', 'admin123')


def get_source_url(suffix, version='v2'):
    BASE_URL = os.environ.get('DEEP_1_URL', 'http://172.21.0.1:9000')
    return '{}/api/{}/{}/'.format(BASE_URL, version, suffix)


def get_migrated_s3_key(s3_url):
    url_data = urlparse(s3_url)
    old_key = unquote(url_data.path)[len('/media/'):]
    return 'deep-v1/{}'.format(old_key)


def is_using_s3():
    return os.environ.get('DJANGO_USE_S3', 'False').lower() == 'true'


def get_migrated_gallery_file(s3_url, title=None):
    if not is_using_s3():
        return None
    if not s3_url:
        return None

    key = get_migrated_s3_key(s3_url)
    if not title:
        title = key.split('/')[-1]

    gallery_file, _ = File.objects.get_or_create(
        file=key,
        defaults={
            'title': title,
        }
    )

    return gallery_file


def request_with_auth(url):
    USERNAME = os.environ.get('DEEP_1_USER', 'test@toggle.com')
    PASSWORD = os.environ.get('DEEP_1_PASSWORD', 'admin123')
    return requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD)).json()
