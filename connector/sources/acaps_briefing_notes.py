from bs4 import BeautifulSoup as Soup
import requests
import datetime

from .base import Source
from lead.models import Lead


class AcapsBriefingNotes(Source):
    URL = 'https://www.acaps.org/special-reports'
    title = 'ACAPS Briefing Notes'
    key = 'acaps-briefing-notes'
    options = [
        {
            'key': 'field_product_status_value',
            'field_type': 'select',
            'title': 'Published date',
            'options': [
                {'key': 'all', 'label': 'Any'},
                {'key': 'upcoming', 'label': 'Upcoming'},
                {'key': 'published', 'label': 'Published'},
            ],
        },
    ]

    def fetch(self, params, page=None, limit=None):
        results = []
        resp = requests.get(self.URL, params=params)
        soup = Soup(resp.text, 'html.parser')
        contents = soup.findAll('div', {'class': 'wrapper-type'})
        if not contents:
            return results
        content = contents[0]
        for item in content.findAll('div', {'class': 'views-row'}):
            try:
                bottomcontent = item.find('div', {'class': 'content-bottom'})
                topcontent = item.find('div', {'class': 'content-top'})
                date = topcontent.find('span', {'class': 'updated-date'}).text
                date = datetime.datetime.strptime(date, '%d/%m/%Y')
                title = topcontent.find('div', {'class': 'field-item'}).text
                link = bottomcontent.find(
                    'div', {'class': 'field-item'}
                ).find('a')
                data = Lead(
                    title=title.strip(),
                    published_on=date,
                    url=link['href'],
                    source='',
                    source_type=''
                )
                results.append(data)
            except Exception as e:
                # Just let it pass
                pass
        return results
