import logging
import requests
from bs4 import BeautifulSoup as Soup
from datetime import datetime

from .base import Source
from connector.utils import handle_connector_parse_error
from lead.models import Lead

logger = logging.getLogger(__name__)


COUNTRIES_OPTIONS = [
    {"key": "afghanistan-181", "label": "Afghanistan"},
    {"key": "bangladesh-199", "label": "Bangladesh"},
    {"key": "burundi-217", "label": "Burundi"},
    {"key": "cameroon-219", "label": "Cameroon"},
    {
        "key": "central-african-republic-223",
        "label": "Central African Republic"
    },
    {"key": "chad-224", "label": "Chad"},
    {"key": "colombia-229", "label": "Colombia"},
    {
        "key": "congo-democratic-republic-63309",
        "label": "Congo, Democratic Republic of the"
    },
    {"key": "ecuador-245", "label": "Ecuador"},
    {"key": "ethiopia-251", "label": "Ethiopia"},
    {"key": "guinea-273", "label": "Guinea"},
    {"key": "haiti-276", "label": "Haiti"},
    {"key": "iraq-286", "label": "Iraq"},
    {"key": "kenya-296", "label": "Kenya"},
    {"key": "liberia-306", "label": "Liberia"},
    {"key": "mali-317", "label": "Mali"},
    {"key": "nepal-336", "label": "Nepal"},
    {"key": "niger-342", "label": "Niger"},
    {"key": "nigeria-343", "label": "Nigeria"},
    {"key": "pakistan-349", "label": "Pakistan"},
    {"key": "philippines-356", "label": "Philippines"},
    {"key": "sierra-leone-380", "label": "Sierra Leone"},
    {"key": "somalia-386", "label": "Somalia"},
    {"key": "south-sudan-391", "label": "South Sudan"},
    {"key": "sudan-392", "label": "Sudan"},
    {"key": "syrian-arab-republic-398", "label": "Syrian Arab Republic"},
    {"key": "ukraine-414", "label": "Ukraine"},
    {"key": "yemen-428", "label": "Yemen"},
]


@handle_connector_parse_error
class HumanitarianResponse(Source):
    URL = 'https://www.humanitarianresponse.info/en/documents/table'
    title = 'Humanitarian Response'
    key = 'humanitarian-response'

    options = [
        {
            'key': 'country',  # key is not used
            'field_type': 'select',
            'title': 'Country',
            'options': COUNTRIES_OPTIONS
        }
    ]

    def fetch(self, params, offset=None, limit=None):
        results = []
        url = self.URL
        if params.get('country'):
            url = self.URL + '/loc/' + params['country']
        resp = requests.get(url, params={})
        soup = Soup(resp.text, 'html.parser')
        contents = soup.find('div', {'id': 'content'}).find('tbody')
        for row in contents.findAll('tr'):
            try:
                tds = row.findAll('td')
                title = tds[0].find('a').get_text().strip()
                datestr = tds[3].get_text().strip()
                date = datetime.strptime(datestr, '%m/%d/%Y')
                url = tds[4].find('a')['href']
                data = {
                    'id': url,
                    'title': title,
                    'published_on': date.date(),
                    'url': url,
                    'source': 'Humanitarian Response',
                    'author': 'Humanitarian Response',
                    'website': self.URL,
                    'source_type': Lead.WEBSITE
                }
                results.append(data)
            except Exception as e:
                logger.warning(
                    "Exception parsing humanitarian response connector: " +
                    str(e.args)
                )

        final_results = results[offset: offset + limit]
        return final_results, len(results)
