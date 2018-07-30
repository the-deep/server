from bs4 import BeautifulSoup as Soup
import requests
import re

from .base import Source
from connector.utils import handle_connector_parse_error
from lead.models import Lead

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


@handle_connector_parse_error
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

    def fetch(self, params, page=None, limit=None):
        country = params.get('country')
        if not country:
            return [], 0
        results = []
        resp = requests.get(self.URL)
        soup = Soup(resp.text, 'html.parser')
        content = soup.find('tbody')
        for row in content.findAll('tr'):
            elem = row.find('a')
            name = elem.get_text()
            name = re.sub('\(.*\)', '', name)
            title = row.findAll('td')[-1].get_text()
            if name.strip() == country.strip():
                # add as lead
                url = elem['href']
                if url[0] == '/':  # means relative path
                    url = self.website + url
                data = Lead(
                    title=title.strip(),
                    url=url,
                    source='PDNA portal',
                    source_type='',
                    website=self.website
                )
                results.append(data)
        return results, len(results)
