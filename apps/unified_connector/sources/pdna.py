import logging
from bs4 import BeautifulSoup as Soup
import requests

from .base import Source
from connector.utils import ConnectorWrapper
from lead.models import Lead

logger = logging.getLogger(__name__)

COUNTRIES_OPTIONS = [
    {'key': 'Somalia', 'label': 'Somalia'},
    {'key': 'Dominica', 'label': 'Dominica'},
    {'key': 'Sri Lanka', 'label': 'Sri Lanka'},
    {'key': 'Sierra Leone', 'label': 'Sierra Leone'},
    {'key': 'Saint Vincent and the Grenadines', 'label': 'Saint Vincent and the Grenadines'},  # noqa
    {'key': 'Vietnam', 'label': 'Vietnam'},
    {'key': 'Seychelles', 'label': 'Seychelles'},
    {'key': 'Fiji', 'label': 'Fiji'},
    {'key': 'Myanmar', 'label': 'Myanmar'},
    {'key': 'Georgia', 'label': 'Georgia'},
    {'key': 'Nepal', 'label': 'Nepal'},
    {'key': 'Vanuatu', 'label': 'Vanuatu'},
    {'key': 'Malawi', 'label': 'Malawi'},
    {'key': 'Cabo Verde', 'label': 'Cabo Verde'},
    {'key': 'St. Vincent and the Grenadines', 'label': 'St. Vincent and the Grenadines'},  # noqa
    {'key': 'Bosnia and Herzegovena', 'label': 'Bosnia and Herzegovena'},
    {'key': 'Burundi ', 'label': 'Burundi '},
    {'key': 'Solomon Islands', 'label': 'Solomon Islands'},
    {'key': 'Burundi ', 'label': 'Burundi '},
    {'key': 'Seychelles', 'label': 'Seychelles'},
    {'key': 'Nigeria', 'label': 'Nigeria'},
    {'key': 'Fiji', 'label': 'Fiji'},
    {'key': 'Samoa', 'label': 'Samoa'},
    {'key': 'Malawi', 'label': 'Malawi'},
    {'key': 'Bhutan', 'label': 'Bhutan'},
    {'key': 'Pakistan', 'label': 'Pakistan'},
    {'key': 'Thailand', 'label': 'Thailand'},
    {'key': 'Djibouti', 'label': 'Djibouti'},
    {'key': 'Kenya', 'label': 'Kenya'},
    {'key': 'Lao PDR', 'label': 'Lao PDR'},
    {'key': 'Lesotho', 'label': 'Lesotho'},
    {'key': 'Uganda', 'label': 'Uganda'},
    {'key': 'Benin', 'label': 'Benin'},
    {'key': 'Guatemala', 'label': 'Guatemala'},
    {'key': 'Togo', 'label': 'Togo'},
    {'key': 'Pakistan', 'label': 'Pakistan'},
    {'key': 'Moldova', 'label': 'Moldova'},
    {'key': 'Haiti', 'label': 'Haiti'},
    {'key': 'El Salvador', 'label': 'El Salvador'},
    {'key': 'Cambodia', 'label': 'Cambodia'},
    {'key': 'Lao PDR', 'label': 'Lao PDR'},
    {'key': 'Indonesia', 'label': 'Indonesia'},
    {'key': 'Samoa', 'label': 'Samoa'},
    {'key': 'Philippines', 'label': 'Philippines'},
    {'key': 'Bhutan', 'label': 'Bhutan'},
    {'key': 'Burkina Faso ', 'label': 'Burkina Faso '},
    {'key': 'Senegal', 'label': 'Senegal'},
    {'key': 'Central African Republic', 'label': 'Central African Republic'},
    {'key': 'Namibia', 'label': 'Namibia'},
    {'key': 'Yemen', 'label': 'Yemen'},
    {'key': 'Haiti', 'label': 'Haiti'},
    {'key': 'India', 'label': 'India'},
    {'key': 'Myanmar', 'label': 'Myanmar'},
    {'key': 'Bolivia', 'label': 'Bolivia'},
    {'key': 'Madagascar', 'label': 'Madagascar'},
    {'key': 'Bangladesh', 'label': 'Bangladesh'}
]


@ConnectorWrapper
class PDNA(Source):
    URL = 'https://www.gfdrr.org/post-disaster-needs-assessments'
    title = 'Post Disaster Needs Assessment'
    key = 'post-disaster-needs-assessment'
    website = 'http://www.gfdrr.org'

    options = [
        {
            'key': 'country',
            'field_type': 'select',
            'title': 'Country',
            'options': COUNTRIES_OPTIONS
        }
    ]

    def get_content(self, url, params):
        resp = requests.get(url)
        return resp.text

    def fetch(self, params):
        print('ffffffffffffffffff', params)
        country = params.get('country')
        if not country:
            return [], 0
        results = []

        content = self.get_content(self.URL, {})
        soup = Soup(content, 'html.parser')

        contents = soup.findAll('tbody')
        for content in contents:
            for row in content.findAll('tr'):
                try:
                    elem = row.find('a')
                    name = elem.get_text()
                    title = row.findAll('td')[-1].get_text()
                    published_on = row.findAll('td')[1].get_text()
                    if name.strip() == country.strip():
                        # add as lead
                        url = elem['href']
                        if url[0] == '/':  # means relative path
                            url = self.website + url
                        data = {
                            'title': title.strip(),
                            'url': url,
                            'source': 'PDNA portal',
                            'author': 'PDNA portal',
                            'published_on': published_on,
                            'source_type': Lead.SourceType.WEBSITE,
                        }
                        results.append(data)

                except Exception as e:
                    logger.warning(
                        "Exception parsing {} with params {}: {}".format(
                            self.URL, params, e.args)
                    )
        return results, len(results)
