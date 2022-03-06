import requests
import datetime
from django.conf import settings

from .base import Source
from .relief_web import COUNTRIES
from connector.utils import ConnectorWrapper


COUNTRIES_OPTIONS = COUNTRIES


def _format_date_or_none(iso_datestr):
    try:
        date = datetime.datetime.strptime(iso_datestr, '%Y-%m-%d')
        return date.strftime('%d-%m-%Y')
    except Exception:
        return None


@ConnectorWrapper
class UNHCRPortal(Source):
    URL = 'https://data.unhcr.org/api-content/documents.json'
    title = 'UNHCR Portal'
    key = 'unhcr-portal'
    options = [
        {
            'key': 'country',
            'field_type': 'select',
            'title': 'Country',
            'options': COUNTRIES_OPTIONS
        },
        {
            'key': 'date_from',
            'field_type': 'date',
            'title': 'From',
        },
        {
            'key': 'date_to',
            'field_type': 'date',
            'title': 'To',
        },
    ]
    params = {
        'API_KEY': settings.UNHCR_PORTAL_API_KEY,
    }

    def get_content(self, url, params):
        return requests.get(url, params=params).json()

    def fetch(self, params):
        results = []
        date_from = _format_date_or_none(params.pop('date_from', None))
        date_to = _format_date_or_none(params.pop('date_to', None))
        if date_from:
            params['global_filter[date_from]'] = date_from
        if date_to:
            params['global_filter[date_to]'] = date_to

        params.update(self.params)  # type is default
        params['limit'] = 50
        page = 0

        while True:
            params['page'] = page
            page += 1
            documents = self.get_content(self.URL, params)
            if not documents:
                break
            for document in documents:
                published_on_raw = document.get('publishDate')
                published_on = published_on_raw and datetime.datetime.fromisoformat(published_on_raw).date()
                data = {
                    'title': document.get('title'),
                    'published_on': published_on,
                    'url': document['downloadLink'],
                    'source': 'UNHCR Portal',
                    'author': '',
                    'source_type': '',
                    'website': 'data2.unhcr.org'
                }
                results.append(data)

        return results, len(results)
