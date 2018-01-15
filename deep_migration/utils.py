from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse, unquote

import requests
import os

from gallery.models import File


# BASE_URL = 'http://www.thedeep.io/api/v2/'
BASE_URL = os.environ.get('DEEP_1_URL', 'http://172.21.0.1:9000/api')
USERNAME = os.environ.get('DEEP_1_USER', 'test@toggle.com')
PASSWORD = os.environ.get('DEEP_1_PASSWORD', 'admin123')


def get_source_url(suffix, version='v2'):
    return '{}/{}/{}/'.format(BASE_URL, version, suffix)


def get_migrated_s3_key(s3_url):
    url_data = urlparse(s3_url)
    old_key = unquote(url_data.path)[len('/media/'):]
    return 'deep-1/{}'.format(old_key)


def is_using_s3():
    return os.environ.get('DJANGO_USE_S3', 'False').lower() == 'true'


def get_migrated_gallery_file(s3_url, title=None):
    if not is_using_s3():
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
    return requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD)).json()
