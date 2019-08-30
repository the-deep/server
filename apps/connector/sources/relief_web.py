import requests

from .base import Source
from lead.models import Lead


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

    def fetch(self, params, offset=None, limit=None):
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

        resp = requests.post(self.URL, json=post_params).json()
        count = resp['totalCount']
        print('LEN', len(resp['data']))
        print('FETCH COUNT', count)

        for datum in resp['data']:
            fields = datum['fields']
            lead = Lead(
                id=str(datum['id']),
                title=fields['title'],
                published_on=fields['date']['original'],
                url=fields['url_alias'],
                source='reliefweb',
                author=fields['source'][0]['name'],
                website='www.reliefweb.int',
            )
            results.append(lead)

        return results, count
