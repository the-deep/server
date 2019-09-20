import requests
import json

from lead.models import Lead
from .base import Source
from connector.utils import ConnectorWrapper


@ConnectorWrapper
class ReliefWeb(Source):
    URL = 'https://api.reliefweb.int/v1/reports?appname=thedeep.io'
    title = 'ReliefWeb Reports'
    key = 'relief-web'
    options = [
        {
            'key': 'country',
            'field_type': 'select',
            'title': 'Country',
            'options': [],
        },
    ]
    filters = [
        {
            'key': 'search',
            'field_type': 'string',
            'title': 'Search',
        },
    ]

    def __init__(self):
        super().__init__()

        from geo.models import Region
        self.options[0]['options'] = [
            {
                'key': r.code,
                'label': r.title,
            } for r in
            Region.objects.filter(public=True)
        ]

    def get_content(self, url, params):
        resp = requests.post(url, json=params)
        return resp.text

    def fetch(self, params, offset, limit):
        results = []

        # Example: http://apidoc.rwlabs.org/#filter

        post_params = {}
        post_params['fields'] = {
            'include': ['url_alias', 'title', 'date.original',
                        'source', 'source.homepage']
        }

        if params.get('country'):
            post_params['filter'] = {
                'field': 'country.iso3',
                'value': params['country'],
            }

        if params.get('search'):
            post_params['query'] = {
                'value': params['search'],
                'fields': ['title'],
                'operator': 'AND',
            }

        if offset:
            post_params['offset'] = offset
        if limit:
            post_params['limit'] = limit

        post_params['sort'] = ['date.original:desc', 'title:asc']

        content = self.get_content(self.URL, post_params)
        resp = json.loads(content)

        total_count = len(resp['data'])
        limited_data = resp['data'][offset: offset + limit]

        for datum in limited_data:
            fields = datum['fields']
            lead = {
                'id': str(datum['id']),
                'title': fields['title'],
                'published_on': fields['date']['original'],
                'url': fields['url_alias'],
                'source': 'reliefweb',
                'source_type': Lead.WEBSITE,
                'author': fields['source'][0]['name'],
                'website': 'www.reliefweb.int',
            }
            results.append(lead)

        return results, total_count
