import requests
import json

from lead.models import Lead
from .base import Source
from connector.utils import ConnectorWrapper

from django.conf import settings

COUNTRIES = [
    {"key": "FJI", "label": "Fiji"},
    {"key": "TZA", "label": "Tanzania"},
    {"key": "SAH", "label": "Western Sahara"},
    {"key": "CAN", "label": "Canada"},
    {"key": "USA", "label": "United States of America"},
    {"key": "KAZ", "label": "Kazakhstan"},
    {"key": "UZB", "label": "Uzbekistan"},
    {"key": "PNG", "label": "Bougainville"},
    {"key": "IDN", "label": "Indonesia"},
    {"key": "ARG", "label": "Argentina"},
    {"key": "CHL", "label": "Chile"},
    {"key": "COD", "label": "Democratic Republic of the Congo"},
    {"key": "SOM", "label": "Somalia"},
    {"key": "KEN", "label": "Kenya"},
    {"key": "SDN", "label": "Sudan"},
    {"key": "TCD", "label": "Chad"},
    {"key": "HTI", "label": "Haiti"},
    {"key": "DOM", "label": "Dominican Republic"},
    {"key": "RUS", "label": "Russia"},
    {"key": "BHS", "label": "The Bahamas"},
    {"key": "FLK", "label": "Falkland Islands"},
    {"key": "NOR", "label": "Svalbard"},
    {"key": "GRL", "label": "Greenland"},
    {"key": "ATF", "label": "French Southern and Antarctic Lands"},
    {"key": "TLS", "label": "East Timor"},
    {"key": "ZAF", "label": "South Africa"},
    {"key": "LSO", "label": "Lesotho"},
    {"key": "MEX", "label": "Mexico"},
    {"key": "URY", "label": "Uruguay"},
    {"key": "BRA", "label": "Brazil"},
    {"key": "BOL", "label": "Bolivia"},
    {"key": "PER", "label": "Peru"},
    {"key": "COL", "label": "Colombia"},
    {"key": "PAN", "label": "Panama"},
    {"key": "CRI", "label": "Costa Rica"},
    {"key": "NIC", "label": "Nicaragua"},
    {"key": "HND", "label": "Honduras"},
    {"key": "SLV", "label": "El Salvador"},
    {"key": "GTM", "label": "Guatemala"},
    {"key": "BLZ", "label": "Belize"},
    {"key": "VEN", "label": "Venezuela"},
    {"key": "GUY", "label": "Guyana"},
    {"key": "SUR", "label": "Suriname"},
    {"key": "FRA", "label": "France"},
    {"key": "ECU", "label": "Ecuador"},
    {"key": "PRI", "label": "Puerto Rico"},
    {"key": "JAM", "label": "Jamaica"},
    {"key": "CUB", "label": "Cuba"},
    {"key": "ZWE", "label": "Zimbabwe"},
    {"key": "BWA", "label": "Botswana"},
    {"key": "NAM", "label": "Namibia"},
    {"key": "SEN", "label": "Senegal"},
    {"key": "MLI", "label": "Mali"},
    {"key": "MRT", "label": "Mauritania"},
    {"key": "BEN", "label": "Benin"},
    {"key": "NER", "label": "Niger"},
    {"key": "NGA", "label": "Nigeria"},
    {"key": "CMR", "label": "Cameroon"},
    {"key": "TGO", "label": "Togo"},
    {"key": "GHA", "label": "Ghana"},
    {"key": "CIV", "label": "Ivory Coast"},
    {"key": "GIN", "label": "Guinea"},
    {"key": "GNB", "label": "Guinea Bissau"},
    {"key": "LBR", "label": "Liberia"},
    {"key": "SLE", "label": "Sierra Leone"},
    {"key": "BFA", "label": "Burkina Faso"},
    {"key": "CAF", "label": "Central African Republic"},
    {"key": "COG", "label": "Republic of the Congo"},
    {"key": "GAB", "label": "Gabon"},
    {"key": "GNQ", "label": "Equatorial Guinea"},
    {"key": "ZMB", "label": "Zambia"},
    {"key": "MWI", "label": "Malawi"},
    {"key": "MOZ", "label": "Mozambique"},
    {"key": "SWZ", "label": "Swaziland"},
    {"key": "AGO", "label": "Angola"},
    {"key": "BDI", "label": "Burundi"},
    {"key": "ISR", "label": "Israel"},
    {"key": "LBN", "label": "Lebanon"},
    {"key": "MDG", "label": "Madagascar"},
    {"key": "PSX", "label": "West Bank"},
    {"key": "GMB", "label": "Gambia"},
    {"key": "TUN", "label": "Tunisia"},
    {"key": "DZA", "label": "Algeria"},
    {"key": "JOR", "label": "Jordan"},
    {"key": "ARE", "label": "United Arab Emirates"},
    {"key": "QAT", "label": "Qatar"},
    {"key": "KWT", "label": "Kuwait"},
    {"key": "IRQ", "label": "Iraq"},
    {"key": "OMN", "label": "Oman"},
    {"key": "VUT", "label": "Vanuatu"},
    {"key": "KHM", "label": "Cambodia"},
    {"key": "THA", "label": "Thailand"},
    {"key": "LAO", "label": "Laos"},
    {"key": "MMR", "label": "Myanmar"},
    {"key": "VNM", "label": "Vietnam"},
    {"key": "PRK", "label": "North Korea"},
    {"key": "KOR", "label": "South Korea"},
    {"key": "MNG", "label": "Mongolia"},
    {"key": "IND", "label": "India"},
    {"key": "BGD", "label": "Bangladesh"},
    {"key": "BTN", "label": "Bhutan"},
    {"key": "NPL", "label": "Nepal"},
    {"key": "PAK", "label": "Pakistan"},
    {"key": "AFG", "label": "Afghanistan"},
    {"key": "TJK", "label": "Tajikistan"},
    {"key": "KGZ", "label": "Kyrgyzstan"},
    {"key": "TKM", "label": "Turkmenistan"},
    {"key": "IRN", "label": "Iran"},
    {"key": "SYR", "label": "Syria"},
    {"key": "ARM", "label": "Armenia"},
    {"key": "SWE", "label": "Sweden"},
    {"key": "BLR", "label": "Belarus"},
    {"key": "UKR", "label": "Ukraine"},
    {"key": "POL", "label": "Poland"},
    {"key": "AUT", "label": "Austria"},
    {"key": "HUN", "label": "Hungary"},
    {"key": "MDA", "label": "Moldova"},
    {"key": "ROU", "label": "Romania"},
    {"key": "LTU", "label": "Lithuania"},
    {"key": "LVA", "label": "Latvia"},
    {"key": "EST", "label": "Estonia"},
    {"key": "DEU", "label": "Germany"},
    {"key": "BGR", "label": "Bulgaria"},
    {"key": "GRC", "label": "Greece"},
    {"key": "TUR", "label": "Turkey"},
    {"key": "ALB", "label": "Albania"},
    {"key": "HRV", "label": "Croatia"},
    {"key": "CHE", "label": "Switzerland"},
    {"key": "LUX", "label": "Luxembourg"},
    {"key": "BEL", "label": "Belgium"},
    {"key": "NLD", "label": "Netherlands"},
    {"key": "PRT", "label": "Portugal"},
    {"key": "ESP", "label": "Spain"},
    {"key": "IRL", "label": "Ireland"},
    {"key": "NCL", "label": "New Caledonia"},
    {"key": "SLB", "label": "Solomon Islands"},
    {"key": "NZL", "label": "New Zealand"},
    {"key": "AUS", "label": "Australia"},
    {"key": "LKA", "label": "Sri Lanka"},
    {"key": "CHN", "label": "China"},
    {"key": "TWN", "label": "Taiwan"},
    {"key": "ITA", "label": "Italy"},
    {"key": "DNK", "label": "Denmark"},
    {"key": "GBR", "label": "Scotland"},
    {"key": "ISL", "label": "Iceland"},
    {"key": "AZE", "label": "Azerbaijan"},
    {"key": "GEO", "label": "Georgia"},
    {"key": "PHL", "label": "Philippines"},
    {"key": "MYS", "label": "Malaysia"},
    {"key": "BRN", "label": "Brunei"},
    {"key": "SVN", "label": "Slovenia"},
    {"key": "FIN", "label": "Finland"},
    {"key": "SVK", "label": "Slovakia"},
    {"key": "CZE", "label": "Czech Republic"},
    {"key": "ERI", "label": "Eritrea"},
    {"key": "JPN", "label": "Japan"},
    {"key": "PRY", "label": "Paraguay"},
    {"key": "YEM", "label": "Yemen"},
    {"key": "SAU", "label": "Saudi Arabia"},
    {"key": "ATA", "label": "Antarctica"},
    {"key": "CYN", "label": "Northern Cyprus"},
    {"key": "CYP", "label": "Cyprus"},
    {"key": "MAR", "label": "Western Sahara"},
    {"key": "EGY", "label": "Egypt"},
    {"key": "LBY", "label": "Libya"},
    {"key": "ETH", "label": "Ethiopia"},
    {"key": "DJI", "label": "Djibouti"},
    {"key": "SOL", "label": "Somaliland"},
    {"key": "UGA", "label": "Uganda"},
    {"key": "RWA", "label": "Rwanda"},
    {"key": "BIH", "label": "Bosnia and Herzegovina"},
    {"key": "MKD", "label": "Macedonia"},
    {"key": "SRB", "label": "Serbia"},
    {"key": "MNE", "label": "Montenegro"},
    {"key": "KOS", "label": "Kosovo"},
    {"key": "TTO", "label": "Trinidad and Tobago"},
    {"key": "SDS", "label": "South Sudan"},
]


def _format_date(datestr):
    return datestr + 'T00:00:00+00:00'


@ConnectorWrapper
class ReliefWeb(Source):
    URL = f'https://api.reliefweb.int/v1/reports?appname={settings.RELIEFWEB_APPNAME}'
    title = 'ReliefWeb Reports'
    key = 'relief-web'
    options = [
        {
            'key': 'primary-country',
            'field_type': 'select',
            'title': 'Primary Country',
            'options': COUNTRIES,
        },
        {
            'key': 'country',
            'field_type': 'select',
            'title': 'Country',
            'options': COUNTRIES,
        },
        {
            'key': 'from',
            'field_type': 'date',
            'title': 'Reports since'
        },
        {
            'key': 'to',
            'field_type': 'date',
            'title': 'Reports until'
        }
    ]
    filters = [
        {
            'key': 'search',
            'field_type': 'string',
            'title': 'Search',
        },
    ]

    def get_content(self, url, params):
        resp = requests.post(url, json=params)
        return resp.text

    def parse_filter_params(self, params):
        filters = []

        if params.get('country'):
            filters.append({'field': 'country.iso3', 'value': params['country']})
        if params.get('primary-country'):
            filters.append({'field': 'primary_country.iso3', 'value': params['primary-country']})

        date_filter = {}
        # If date is obtained, it must be formatted to the ISO string with timezone info
        # the _format_date just appends 00:00:00 Time and +00:00 tz info
        if params.get('from'):
            date_filter['from'] = _format_date(params['from'])
        if params.get('to'):
            date_filter["to"] = _format_date(params['to'])
        if date_filter:
            filters.append({'field': 'date.original', 'value': date_filter})

        if filters:
            return {'operator': 'AND', 'conditions': filters}
        return {}

    def fetch(self, params, offset, limit):
        results = []

        post_params = {}
        post_params['fields'] = {
            'include': ['url_alias', 'title', 'date.original',
                        'source', 'source.homepage']
        }

        post_params['filter'] = self.parse_filter_params(params)

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

        total_count = resp['totalCount']
        limited_data = resp['data']  # The offset limit is handled by the api itself

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
