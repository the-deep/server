import logging
from bs4 import BeautifulSoup as Soup
import requests
import datetime

from .base import Source
from connector.utils import ConnectorWrapper
from lead.models import Lead

logger = logging.getLogger(__name__)

COUNTRIES_OPTIONS = [
    {'key': 'All', 'label': 'Any'},
    {'key': '196', 'label': 'Afghanistan'},
    {'key': '202', 'label': 'Angola'},
    {'key': '214', 'label': 'Bangladesh'},
    {'key': '219', 'label': 'Benin'},
    {'key': '222', 'label': 'Bolivia'},
    {'key': '224', 'label': 'Bosnia and Herzegovina'},
    {'key': '226', 'label': 'Brazil'},
    {'key': '230', 'label': 'Burkina Faso'},
    {'key': '231', 'label': 'Burundi'},
    {'key': '233', 'label': 'Cambodia'},
    {'key': '234', 'label': 'Cameroon'},
    {'key': '237', 'label': 'CAR'},
    {'key': '239', 'label': 'Chad'},
    {'key': '242', 'label': 'China'},
    {'key': '248', 'label': 'Colombia'},
    {'key': '250', 'label': 'Congo'},
    {'key': '253', 'label': "Côte d'Ivoire"},
    {'key': '254', 'label': 'Croatia'},
    {'key': '262', 'label': 'Djibouti'},
    {'key': '263', 'label': 'Dominica'},
    {'key': '264', 'label': 'Dominican Republic'},
    {'key': '259', 'label': 'DPRK'},
    {'key': '260', 'label': 'DRC'},
    {'key': '266', 'label': 'Ecuador'},
    {'key': '267', 'label': 'Egypt'},
    {'key': '268', 'label': 'El Salvador'},
    {'key': '270', 'label': 'Eritrea'},
    {'key': '272', 'label': 'Ethiopia'},
    {'key': '275', 'label': 'Fiji'},
    {'key': '277', 'label': 'France'},
    {'key': '287', 'label': 'Greece'},
    {'key': '292', 'label': 'Guatemala'},
    {'key': '293', 'label': 'Guinea'},
    {'key': '642', 'label': 'Haiti'},
    {'key': '302', 'label': 'India'},
    {'key': '303', 'label': 'Indonesia'},
    {'key': '304', 'label': 'Iran'},
    {'key': '305', 'label': 'Iraq'},
    {'key': '312', 'label': 'Jordan'},
    {'key': '314', 'label': 'Kenya'},
    {'key': '320', 'label': 'Lebanon'},
    {'key': '321', 'label': 'Lesotho'},
    {'key': '322', 'label': 'Liberia'},
    {'key': '323', 'label': 'Libya'},
    {'key': '327', 'label': 'Madagascar'},
    {'key': '329', 'label': 'Malawi'},
    {'key': '332', 'label': 'Mali'},
    {'key': '336', 'label': 'Mauritania'},
    {'key': '339', 'label': 'Mexico'},
    {'key': '343', 'label': 'Mongolia'},
    {'key': '346', 'label': 'Morocco'},
    {'key': '347', 'label': 'Mozambique'},
    {'key': '348', 'label': 'Myanmar'},
    {'key': '349', 'label': 'Namibia'},
    {'key': '351', 'label': 'Nepal'},
    {'key': '356', 'label': 'Nicaragua'},
    {'key': '357', 'label': 'Niger'},
    {'key': '358', 'label': 'Nigeria'},
    {'key': '365', 'label': 'Pakistan'},
    {'key': '363', 'label': 'Palestine'},
    {'key': '368', 'label': 'Papua New Guinea'},
    {'key': '370', 'label': 'Peru'},
    {'key': '371', 'label': 'Philippines'},
    {'key': '381', 'label': 'Rwanda'},
    {'key': '393', 'label': 'Senegal'},
    {'key': '394', 'label': 'Serbia'},
    {'key': '396', 'label': 'Sierra Leone'},
    {'key': '400', 'label': 'Slovenia'},
    {'key': '402', 'label': 'Somalia'},
    {'key': '404', 'label': 'South Sudan'},
    {'key': '406', 'label': 'Sri Lanka'},
    {'key': '407', 'label': 'Sudan'},
    {'key': '410', 'label': 'Swaziland'},
    {'key': '194', 'label': 'Syria'},
    {'key': '413', 'label': 'Tajikistan'},
    {'key': '415', 'label': 'the former Yugoslav Republic of Macedonia'},
    {'key': '282', 'label': 'The Gambia'},
    {'key': '416', 'label': 'Timor-Leste'},
    {'key': '419', 'label': 'Tonga'},
    {'key': '422', 'label': 'Turkey'},
    {'key': '426', 'label': 'Uganda'},
    {'key': '427', 'label': 'Ukraine'},
    {'key': '435', 'label': 'Vanuatu'},
    {'key': '436', 'label': 'Venezuela'},
    {'key': '437', 'label': 'Vietnam'},
    {'key': '457', 'label': 'Yemen'},
    {'key': '442', 'label': 'Zambia'},
    {'key': '443', 'label': 'Zimbabwe'}
]


@ConnectorWrapper
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
                {'key': 'All', 'label': 'Any'},
                {'key': 'upcoming', 'label': 'Upcoming'},
                {'key': 'published', 'label': 'Published'},
            ],
        },
        {
            'key': 'field_countries_target_id',
            'field_type': 'select',
            'title': 'Country',
            'options': COUNTRIES_OPTIONS
        },
        {
            'key': 'field_product_category_target_id',
            'field_type': 'select',
            'title': 'Type of Report',
            'options': [
                {'key': 'All', 'label': 'Any'},
                {'key': '281', 'label': 'Short notes'},
                {'key': '279', 'label': 'Briefing notes'},
                {'key': '280', 'label': 'Crisis profiles'},
                {'key': '282', 'label': 'Thematic reports'},
            ]
        }
    ]

    def get_content(self, url, params):
        resp = requests.get(url, params=params)
        return resp.text

    def fetch(self, params, offset, limit):
        results = []
        content = self.get_content(self.URL, params)
        soup = Soup(content, 'html.parser')
        contents = soup.findAll('div', {'class': 'wrapper-type'})
        if not contents:
            return results, 0

        content = contents[0]
        for item in content.findAll('div', {'class': 'views-row'}):
            try:
                bottomcontent = item.find('div', {'class': 'content-bottom'})
                topcontent = item.find('div', {'class': 'content-top'})
                date = topcontent.find('span', {'class': 'updated-date'}).text
                date = datetime.datetime.strptime(date, '%d/%m/%Y')
                title = topcontent.find('div', {'class': 'field-item'}).text
                link_elem = bottomcontent.find(
                    'div', {'class': 'field-item'}
                )
                link = link_elem.find('a')
                data = {
                    'title': title.strip(),
                    'published_on': date.date(),
                    'url': link['href'],
                    'source': 'Briefing Notes',
                    'source_type': Lead.WEBSITE,
                    'website': 'www.acaps.org/special-reports'
                }
                results.append(data)
            except Exception as e:
                logger.warning(
                    "Exception parsing {} with params {}: {}".format(
                        self.URL, params, e.args)
                )

        final_results = results[offset: offset + limit]
        return final_results, len(results)
