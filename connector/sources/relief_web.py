import requests

from .base import Source
from lead.models import Lead


class ReliefWeb(Source):
    URL = 'https://api.reliefweb.int/v1/reports'
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

    def __init__(self):
        super(ReliefWeb, self).__init__()

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

        if offset:
            post_params['offset'] = offset
        if limit:
            post_params['limit'] = limit

        resp = requests.post(self.URL, json=post_params).json()
        count = resp['totalCount']

        for datum in resp['data']:
            fields = datum['fields']
            lead = Lead(
                title=fields['title'],
                published_on=fields['date']['original'],
                url=fields['url_alias'],
                source=fields['source'][0]['name'],
                website='www.reliefweb.int',
            )
            results.append(lead)

        return results, count
