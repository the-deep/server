import re
from urllib.parse import urlparse
import requests
from organization.models import Organization


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36', # noqa
}


class RedhumWebInfoExtractor:
    def __init__(self, url):
        self.url = url
        self.page = {}
        url_parse = re.search(r'https://redhum.org/documento/(?P<report_id>\d+)\/?$', url)
        if not url_parse:
            return
        report_id = url_parse.group('report_id')
        rw_url = f'https://api.reliefweb.int/v1/reports/{report_id}'
        params = {
            'appname': 'redhum',
            'fields[include][]': ['title', 'primary_country', 'source', 'date', 'body-html'],
        }

        try:
            response = requests.get(rw_url, headers=HEADERS, params=params)
            self.page = response.json()['data'][0]['fields']
        except Exception:
            return

    def get_title(self):
        return self.page.get('title')

    def get_date(self):
        return self.page.get('date', {}).get('created', '').split('T')[0]

    def get_country(self):
        return self.page.get('primary_country', {}).get('name')

    def get_source(self):
        return {
            'text': 'redhum',
        }

    def get_author(self):
        source = (self.page.get('source') or [{}])[0]
        return {
            'relief_web_id': source.get('id'),
            'text': source.get('longname'),
        }

    def get_website(self):
        return urlparse(self.url).netloc

    def get_content(self):
        return self.page.get('body-html', '')
