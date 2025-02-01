import json
import copy
import logging

import requests
import datetime

from bs4 import BeautifulSoup as Soup

from utils.common import deep_date_format
from connector.utils import ConnectorWrapper

from .base import Source
logger = logging.Logger(__name__)

COUNTRIES_OPTIONS = [
    {"label": "All", "key": ""},
    {"label": "Afghanistan", "key": "575"},
    {"label": "Albania", "key": "576"},
    {"label": "Algeria", "key": "769"},
    {"label": "Andorra", "key": "577"},
    {"label": "Angola", "key": "578"},
    {"label": "Antigua and Barbuda", "key": "579"},
    {"label": "Argentina", "key": "580"},
    {"label": "Armenia", "key": "581"},
    {"label": "Aruba", "key": "11773"},
    {"label": "Australia", "key": "582"},
    {"label": "Austria", "key": "583"},
    {"label": "Azerbaijan", "key": "584"},
    {"label": "Bahamas", "key": "592"},
    {"label": "Bahrain", "key": "585"},
    {"label": "Bangladesh", "key": "591"},
    {"label": "Barbados", "key": "586"},
    {"label": "Belarus", "key": "595"},
    {"label": "Belgium", "key": "588"},
    {"label": "Belize", "key": "602"},
    {"label": "Benin", "key": "589"},
    {"label": "Bhutan", "key": "593"},
    {"label": "Bolivia (Plurinational State of)", "key": "596"},
    {"label": "Bosnia and Herzegovina", "key": "600"},
    {"label": "Botswana", "key": "597"},
    {"label": "Brazil", "key": "598"},
    {"label": "Brunei Darussalam", "key": "599"},
    {"label": "Bulgaria", "key": "601"},
    {"label": "Burkina Faso", "key": "594"},
    {"label": "Burundi", "key": "587"},
    {"label": "Cabo Verde", "key": "615"},
    {"label": "Cambodia", "key": "603"},
    {"label": "Cameroon", "key": "349"},
    {"label": "Canada", "key": "604"},
    {"label": "Central African Republic", "key": "399"},
    {"label": "Chad", "key": "410"},
    {"label": "Chile", "key": "607"},
    {"label": "China", "key": "606"},
    {"label": "Colombia", "key": "612"},
    {"label": "Comoros", "key": "610"},
    {"label": "Costa Rica", "key": "613"},
    {"label": "Cote d'Ivoire", "key": "509"},
    {"label": "Croatia", "key": "648"},
    {"label": "Cuba", "key": "614"},
    {"label": "Curaçao", "key": "11774"},
    {"label": "Cyprus", "key": "616"},
    {"label": "Czech Republic", "key": "617"},
    {"label": "Democratic People's Republic of Korea", "key": "663"},
    {"label": "Democratic Republic of the Congo", "key": "486"},
    {"label": "Denmark", "key": "618"},
    {"label": "Djibouti", "key": "151"},
    {"label": "Dominica", "key": "619"},
    {"label": "Dominican Republic", "key": "620"},
    {"label": "Ecuador", "key": "621"},
    {"label": "Egypt", "key": "1"},
    {"label": "El Salvador", "key": "720"},
    {"label": "Equatorial Guinea", "key": "622"},
    {"label": "Eritrea", "key": "157"},
    {"label": "Estonia", "key": "623"},
    {"label": "Ethiopia", "key": "160"},
    {"label": "Fiji", "key": "625"},
    {"label": "Finland", "key": "626"},
    {"label": "France", "key": "629"},
    {"label": "Gabon", "key": "632"},
    {"label": "Gambia", "key": "633"},
    {"label": "Georgia", "key": "635"},
    {"label": "Germany", "key": "636"},
    {"label": "Ghana", "key": "637"},
    {"label": "Greece", "key": "640"},
    {"label": "Grenada", "key": "641"},
    {"label": "Guatemala", "key": "642"},
    {"label": "Guinea", "key": "643"},
    {"label": "Guinea-Bissau", "key": "639"},
    {"label": "Guyana", "key": "644"},
    {"label": "Haiti", "key": "645"},
    {"label": "Holy See", "key": "756"},
    {"label": "Honduras", "key": "647"},
    {"label": "Hungary", "key": "649"},
    {"label": "Iceland", "key": "650"},
    {"label": "India", "key": "651"},
    {"label": "Indonesia", "key": "652"},
    {"label": "Iran (Islamic Republic of)", "key": "654"},
    {"label": "Iraq", "key": "5"},
    {"label": "Ireland", "key": "653"},
    {"label": "Israel", "key": "655"},
    {"label": "Italy", "key": "656"},
    {"label": "Jamaica", "key": "657"},
    {"label": "Japan", "key": "658"},
    {"label": "Jordan", "key": "36"},
    {"label": "Kazakhstan", "key": "659"},
    {"label": "Kenya", "key": "178"},
    {"label": "Kiribati", "key": "661"},
    {"label": "Kuwait", "key": "664"},
    {"label": "Kyrgyzstan", "key": "660"},
    {"label": "Lao People's Democratic Republic", "key": "665"},
    {"label": "Latvia", "key": "673"},
    {"label": "Lebanon", "key": "71"},
    {"label": "Lesotho", "key": "668"},
    {"label": "Liberia", "key": "535"},
    {"label": "Libya", "key": "666"},
    {"label": "Liechtenstein", "key": "669"},
    {"label": "Lithuania", "key": "671"},
    {"label": "Luxembourg", "key": "672"},
    {"label": "Madagascar", "key": "675"},
    {"label": "Malawi", "key": "686"},
    {"label": "Malaysia", "key": "685"},
    {"label": "Maldives", "key": "681"},
    {"label": "Mali", "key": "684"},
    {"label": "Malta", "key": "690"},
    {"label": "Marshall Islands", "key": "683"},
    {"label": "Mauritania", "key": "677"},
    {"label": "Mauritius", "key": "692"},
    {"label": "Mexico", "key": "682"},
    {"label": "Micronesia (Federated States of)", "key": "631"},
    {"label": "Monaco", "key": "679"},
    {"label": "Mongolia", "key": "687"},
    {"label": "Montenegro", "key": "691"},
    {"label": "Morocco", "key": "688"},
    {"label": "Mozambique", "key": "689"},
    {"label": "Myanmar", "key": "693"},
    {"label": "Namibia", "key": "694"},
    {"label": "Nauru", "key": "702"},
    {"label": "Nepal", "key": "695"},
    {"label": "Netherlands", "key": "696"},
    {"label": "New Zealand", "key": "703"},
    {"label": "Nicaragua", "key": "698"},
    {"label": "Niger", "key": "697"},
    {"label": "Nigeria", "key": "699"},
    {"label": "Norway", "key": "701"},
    {"label": "Oman", "key": "704"},
    {"label": "Other (North Africa)", "key": "10006"},
    {"label": "Other (Sub-Saharan Africa)", "key": "10004"},
    {"label": "Pakistan", "key": "705"},
    {"label": "Palau", "key": "710"},
    {"label": "Panama", "key": "706"},
    {"label": "Papua New Guinea", "key": "711"},
    {"label": "Paraguay", "key": "707"},
    {"label": "Peru", "key": "708"},
    {"label": "Philippines", "key": "709"},
    {"label": "Poland", "key": "712"},
    {"label": "Portugal", "key": "713"},
    {"label": "Qatar", "key": "715"},
    {"label": "Republic of Korea", "key": "662"},
    {"label": "Republic of Moldova", "key": "680"},
    {"label": "Republic of the Congo", "key": "476"},
    {"label": "Romania", "key": "716"},
    {"label": "Russian Federation", "key": "718"},
    {"label": "Rwanda", "key": "719"},
    {"label": "Saint Kitts and Nevis", "key": "731"},
    {"label": "Saint Lucia", "key": "667"},
    {"label": "Saint Vincent and the Grenadines", "key": "757"},
    {"label": "Samoa", "key": "759"},
    {"label": "San Marino", "key": "727"},
    {"label": "Sao Tome and Principe", "key": "732"},
    {"label": "Saudi Arabia", "key": "721"},
    {"label": "Senegal", "key": "723"},
    {"label": "Serbia", "key": "722"},
    {"label": "Seychelles", "key": "724"},
    {"label": "Sierra Leone", "key": "726"},
    {"label": "Singapore", "key": "725"},
    {"label": "Slovakia", "key": "734"},
    {"label": "Slovenia", "key": "735"},
    {"label": "Solomon Islands", "key": "728"},
    {"label": "Somalia", "key": "192"},
    {"label": "South Africa", "key": "717"},
    {"label": "South Sudan", "key": "259"},
    {"label": "Spain", "key": "729"},
    {"label": "Sri Lanka", "key": "670"},
    {"label": "Sudan", "key": "295"},
    {"label": "Suriname", "key": "733"},
    {"label": "Swaziland", "key": "736"},
    {"label": "Sweden", "key": "737"},
    {"label": "Switzerland", "key": "738"},
    {"label": "Syrian Arab Republic", "key": "112"},
    {"label": "Tajikistan", "key": "742"},
    {"label": "Tanzania (United Republic of)", "key": "217"},
    {"label": "Thailand", "key": "741"},
    {"label": "The former Yugoslav Republic of Macedonia", "key": "678"},
    {"label": "Timor-Leste", "key": "744"},
    {"label": "Togo", "key": "745"},
    {"label": "Tonga", "key": "746"},
    {"label": "Trinidad and Tobago", "key": "747"},
    {"label": "Tunisia", "key": "748"},
    {"label": "Turkey", "key": "113"},
    {"label": "Turkmenistan", "key": "743"},
    {"label": "Tuvalu", "key": "749"},
    {"label": "Uganda", "key": "220"},
    {"label": "Ukraine", "key": "751"},
    {"label": "United Arab Emirates", "key": "750"},
    {"label": "United Kingdom", "key": "634"},
    {"label": "United States of America", "key": "753"},
    {"label": "Uruguay", "key": "752"},
    {"label": "Uzbekistan", "key": "754"},
    {"label": "Vanuatu", "key": "755"},
    {"label": "Venezuela", "key": "758"},
    {"label": "Viet Nam", "key": "730"},
    {"label": "Western Sahara", "key": "760"},
    {"label": "Yemen", "key": "225"},
    {"label": "Zambia", "key": "761"},
    {"label": "Zimbabwe", "key": "762"},
]


def _format_date_or_none(iso_datestr):
    try:
        return deep_date_format(datetime.datetime.strptime(iso_datestr, '%Y-%m-%d'))
    except Exception:
        return None


@ConnectorWrapper
class UNHCRPortal(Source):
    URL = 'https://data2.unhcr.org/en/search'
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
        'type[]': [
            'document',
            # NOTE: for now have only documents as results, other do not seem
            # to be parsable
            # 'link', 'news', 'highlight'
        ]
    }

    def get_content(self, url, params):
        return requests.get(url, params=params).text

    def fetch(self, params):
        results = []
        updated_params = copy.deepcopy(params)

        country = updated_params.pop('country', None)
        date_from = _format_date_or_none(updated_params.pop('date_from', None))
        date_to = _format_date_or_none(updated_params.pop('date_to', None))
        if country:
            updated_params['country_json'] = json.dumps({'0': country})
            updated_params['country'] = country
        if date_from:
            updated_params['date_from'] = date_from
        if date_to:
            updated_params['date_to'] = date_to

        updated_params.update(self.params)  # type is default

        page = 1
        while True:
            if page > self.UNIFIED_CONNECTOR_SOURCE_MAX_PAGE_NUMBER:
                break
            updated_params['page'] = page
            content = self.get_content(self.URL, updated_params)
            soup = Soup(content, 'html.parser')
            contents = soup.findAll('ul', {'class': 'searchResults'})
            if not contents:
                return results, 0

            content = contents[0]
            items = content.findAll('li', {'class': ['searchResultItem']})

            for item in items:
                itemcontent = item.find(
                    'div',
                    {'class': ['searchResultItem_content', 'media_body']}
                )
                urlcontent = item.find(
                    'div',
                    {'class': 'searchResultItem_download'}
                )
                datecontent = item.find(
                    'span',
                    {'class': 'searchResultItem_date'}
                )
                title = itemcontent.find('a').get_text()
                pdfurl = urlcontent.find('a')['href']
                raw_date = datecontent.find('b').get_text()  # 4 July 2018
                date = datetime.datetime.strptime(raw_date, '%d %B %Y')
                data = {
                    'title': title and title.strip(),
                    'published_on': date.date(),
                    'url': pdfurl,
                    'source': 'UNHCR Portal',
                    'author': '',
                    'source_type': '',
                }
                results.append(data)
            logger.info(f'the resulted data of unhcr is: {results}')
            footer = soup.find('div', {'class': 'pgSearch_results_footer'})
            if not footer:
                break
            next_url = footer.find('a', {'rel': 'next'})
            if next_url and next_url['href']:
                page += 1
            else:
                break
        return results, len(results)
