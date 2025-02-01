import requests
import json

from lead.models import Lead
from .base import Source
from connector.utils import ConnectorWrapper

from django.conf import settings

# NOTE: Generated using scripts/list_relief_web_countries.sh
COUNTRIES_LIST = [
    ("BES", "Bonaire, Saint Eustatius and Saba (The Netherlands)"),
    ("MAF", "Saint Martin (France)"),
    ("WLF", "Wallis and Futuna (France)"),
    ("ARE", "United Arab Emirates"),
    ("TLS", "Timor-Leste"),
    ("SGP", "Singapore"),
    ("SHN", "Saint Helena"),
    ("REU", "Réunion (France)"),
    ("QAT", "Qatar"),
    ("PCN", "Pitcairn Islands"),
    ("LUX", "Luxembourg"),
    ("KWT", "Kuwait"),
    ("JAM", "Jamaica"),
    ("GIB", "Gibraltar"),
    ("GAB", "Gabon"),
    ("FRO", "Faroe Islands (Denmark)"),
    ("EAI", "Easter Island (Chile)"),
    ("CIV", "Côte d'Ivoire"),
    ("CXR", "Christmas Island (Australia)"),
    ("TWN", "China - Taiwan Province"),
    ("HKG", "China - Hong Kong (Special Administrative Region)"),
    ("CHI", "Channel Islands"),
    ("CYM", "Cayman Islands"),
    ("CAI", "Canary Islands (Spain)"),
    ("BRN", "Brunei Darussalam"),
    ("VGB", "British Virgin Islands"),
    ("COM", "Comoros"),
    ("CPV", "Cabo Verde"),
    ("BWA", "Botswana"),
    ("GHA", "Ghana"),
    ("MUS", "Mauritius"),
    ("GUY", "Guyana"),
    ("GRC", "Greece"),
    ("MNG", "Mongolia"),
    ("JPN", "Japan"),
    ("PNG", "Papua New Guinea"),
    ("NZL", "New Zealand"),
    ("FSM", "Micronesia (Federated States of)"),
    ("COK", "Cook Islands"),
    ("WSM", "Samoa"),
    ("TON", "Tonga"),
    ("TKM", "Turkmenistan"),
    ("KAZ", "Kazakhstan"),
    ("UZB", "Uzbekistan"),
    ("ARG", "Argentina"),
    ("MYS", "Malaysia"),
    ("CHL", "Chile"),
    ("BRA", "Brazil"),
    ("ABW", "Aruba (The Netherlands)"),
    ("CUW", "Curaçao (The Netherlands)"),
    ("AUT", "Austria"),
    ("CYP", "Cyprus"),
    ("EST", "Estonia"),
    ("ECU", "Ecuador"),
    ("GEO", "Georgia"),
    ("FRA", "France"),
    ("LVA", "Latvia"),
    ("PRY", "Paraguay"),
    ("LTU", "Lithuania"),
    ("SVK", "Slovakia"),
    ("NLD", "Netherlands"),
    ("NOR", "Norway"),
    ("RUS", "Russian Federation"),
    ("SWE", "Sweden"),
    ("SRB", "Serbia"),
    ("TTO", "Trinidad and Tobago"),
    ("GBR", "United Kingdom of Great Britain and Northern Ireland"),
    ("GTM", "Guatemala"),
    ("USA", "United States of America"),
    ("MDG", "Madagascar"),
    ("DJI", "Djibouti"),
    ("JOR", "Jordan"),
    ("LKA", "Sri Lanka"),
    ("HTI", "Haiti"),
    ("KEN", "Kenya"),
    ("ZWE", "Zimbabwe"),
    ("COD", "Democratic Republic of the Congo"),
    ("NER", "Niger"),
    ("PHL", "Philippines"),
    ("TUR", "Türkiye"),
    ("NPL", "Nepal"),
    ("SYR", "Syrian Arab Republic"),
    ("CAF", "Central African Republic"),
    ("SOM", "Somalia"),
    ("IRQ", "Iraq"),
    ("YEM", "Yemen"),
    ("PSE", "occupied Palestinian territory"),
    ("AFG", "Afghanistan"),
    ("BLM", "Saint Barthélemy (France)"),
    ("TCA", "Turks and Caicos Islands"),
    ("TKL", "Tokelau"),
    ("VCT", "Saint Vincent and the Grenadines"),
    ("KNA", "Saint Kitts and Nevis"),
    ("PRI", "Puerto Rico (The United States of America)"),
    ("MNP", "Northern Mariana Islands (The United States of America)"),
    ("NFK", "Norfolk Island (Australia)"),
    ("NCL", "New Caledonia (France)"),
    ("MSR", "Montserrat"),
    ("MCO", "Monaco"),
    ("MYT", "Mayotte (France)"),
    ("MLT", "Malta"),
    ("MDV", "Maldives"),
    ("LAO", "Lao People's Democratic Republic (the)"),
    ("VAT", "Holy See"),
    ("GUM", "Guam"),
    ("GLI", "Galapagos Islands (Ecuador)"),
    ("FLK", "Falkland Islands (Malvinas)"),
    ("DMA", "Dominica"),
    ("MAC", "China - Macau (Special Administrative Region)"),
    ("BHR", "Bahrain"),
    ("AZO", "Azores Islands (Portugal)"),
    ("ATG", "Antigua and Barbuda"),
    ("AIA", "Anguilla"),
    ("ALA", "Aland Islands (Finland)"),
    ("ZAF", "South Africa"),
    ("NAM", "Namibia"),
    ("KHM", "Cambodia"),
    ("GNB", "Guinea-Bissau"),
    ("ERI", "Eritrea"),
    ("GNQ", "Equatorial Guinea"),
    ("LSO", "Lesotho"),
    ("IDN", "Indonesia"),
    ("FJI", "Fiji"),
    ("KOR", "Republic of Korea"),
    ("NRU", "Nauru"),
    ("SLB", "Solomon Islands"),
    ("TUV", "Tuvalu"),
    ("PLW", "Palau"),
    ("ALB", "Albania"),
    ("BOL", "Bolivia (Plurinational State of)"),
    ("BIH", "Bosnia and Herzegovina"),
    ("BEL", "Belgium"),
    ("SLV", "El Salvador"),
    ("DOM", "Dominican Republic"),
    ("GMB", "Gambia"),
    ("DEU", "Germany"),
    ("HUN", "Hungary"),
    ("ITA", "Italy"),
    ("IRL", "Ireland"),
    ("POL", "Poland"),
    ("MKD", "the Republic of North Macedonia"),
    ("PAN", "Panama"),
    ("ROU", "Romania"),
    ("PRT", "Portugal"),
    ("CHE", "Switzerland"),
    ("LIE", "Liechtenstein"),
    ("AGO", "Angola"),
    ("ZMB", "Zambia"),
    ("RWA", "Rwanda"),
    ("MRT", "Mauritania"),
    ("SEN", "Senegal"),
    ("BDI", "Burundi"),
    ("ARM", "Armenia"),
    ("MLI", "Mali"),
    ("SSD", "South Sudan"),
    ("EGY", "Egypt"),
    ("CMR", "Cameroon"),
    ("MEX", "Mexico"),
    ("CRI", "Costa Rica"),
    ("CHN", "China"),
    ("PAK", "Pakistan"),
    ("MOZ", "Mozambique"),
    ("UKR", "Ukraine"),
    ("LBN", "Lebanon"),
    ("VUT", "Vanuatu"),
    ("LBY", "Libya"),
    ("COL", "Colombia"),
    ("SXM", "Sint Maarten (The Netherlands)"),
    ("ESH", "Western Sahara"),
    ("VIR", "United States Virgin Islands"),
    ("TGO", "Togo"),
    ("SJM", "Svalbard and Jan Mayen Islands"),
    ("SUR", "Suriname"),
    ("SVN", "Slovenia"),
    ("SYC", "Seychelles"),
    ("STP", "Sao Tome and Principe"),
    ("SMR", "San Marino"),
    ("SPM", "Saint Pierre and Miquelon (France)"),
    ("LCA", "Saint Lucia"),
    ("OMN", "Oman"),
    ("ANT", "Netherlands Antilles (The Netherlands)"),
    ("MTQ", "Martinique (France)"),
    ("MDR", "Madeira (Portugal)"),
    ("ILM", "Isle of Man (The United Kingdom of Great Britain and Northern Ireland)"),
    ("HMD", "Heard Island and McDonald Islands (Australia)"),
    ("GLP", "Guadeloupe (France)"),
    ("GRD", "Grenada"),
    ("GRL", "Greenland (Denmark)"),
    ("PYF", "French Polynesia (France)"),
    ("GUF", "French Guiana (France)"),
    ("CCK", "Cocos (Keeling) Islands (Australia)"),
    ("BTN", "Bhutan"),
    ("BMU", "Bermuda"),
    ("BRB", "Barbados"),
    ("BHS", "Bahamas"),
    ("AND", "Andorra"),
    ("ASM", "American Samoa"),
    ("THA", "Thailand"),
    ("AZE", "Azerbaijan"),
    ("WLD", "World"),
    ("TZA", "United Republic of Tanzania"),
    ("SWZ", "Eswatini"),
    ("NIC", "Nicaragua"),
    ("KGZ", "Kyrgyzstan"),
    ("IND", "India"),
    ("AUS", "Australia"),
    ("NIU", "Niue (New Zealand)"),
    ("MHL", "Marshall Islands"),
    ("KIR", "Kiribati"),
    ("TJK", "Tajikistan"),
    ("DZA", "Algeria"),
    ("BLR", "Belarus"),
    ("BLZ", "Belize"),
    ("BGR", "Bulgaria"),
    ("HRV", "Croatia"),
    ("CAN", "Canada"),
    ("CZE", "Czechia"),
    ("CUB", "Cuba"),
    ("DNK", "Denmark"),
    ("FIN", "Finland"),
    ("ISL", "Iceland"),
    ("PER", "Peru"),
    ("MDA", "Moldova"),
    ("MNE", "Montenegro"),
    ("SAU", "Saudi Arabia"),
    ("URY", "Uruguay"),
    ("TUN", "Tunisia"),
    ("ESP", "Spain"),
    ("VEN", "Venezuela (Bolivarian Republic of)"),
    ("BEN", "Benin"),
    ("PRK", "Democratic People's Republic of Korea"),
    ("GIN", "Guinea"),
    ("VNM", "Viet Nam"),
    ("MWI", "Malawi"),
    ("COG", "Congo"),
    ("MAR", "Morocco"),
    ("SLE", "Sierra Leone"),
    ("ISR", "Israel"),
    ("ETH", "Ethiopia"),
    ("NGA", "Nigeria"),
    ("SDN", "Sudan"),
    ("BGD", "Bangladesh"),
    ("TCD", "Chad"),
    ("MMR", "Myanmar"),
    ("UGA", "Uganda"),
    ("HND", "Honduras"),
    ("IRN", "Iran (Islamic Republic of)"),
    ("LBR", "Liberia"),
    ("BFA", "Burkina Faso"),
]


COUNTRIES = [
    {
        "key": iso3,
        "label": name,
    }
    for iso3, name in COUNTRIES_LIST
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
        print('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
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

    def fetch(self, params):
        results = []

        post_params = {}
        post_params['fields'] = {
            'include': [
                'url_alias', 'title', 'date.original', 'file', 'source', 'source.homepage'
            ]
        }

        post_params['filter'] = self.parse_filter_params(params)

        if params.get('search'):
            post_params['query'] = {
                'value': params['search'],
                'fields': ['title'],
                'operator': 'AND',
            }

        post_params['limit'] = 1000
        post_params['sort'] = ['date.original:desc', 'title:asc']

        relief_url = self.URL
        total_count = 0

        while relief_url is not None:
            content = self.get_content(relief_url, post_params)
            resp = json.loads(content)
            total_count += resp['totalCount']

            for datum in resp['data']:
                fields = datum['fields']
                url = fields['file'][0]['url'] if fields.get('file') else fields['url_alias']
                title = fields['title']
                published_on = (fields.get('date') or {}).get('original')
                author = ((fields.get('source') or [{}])[0] or {}).get('name')
                lead = {
                    'id': str(datum['id']),
                    'title': title,
                    'published_on': published_on,
                    'url': url,
                    'source': 'reliefweb',
                    'source_type': Lead.SourceType.WEBSITE.value,
                    'author': author,
                }
                results.append(lead)
            relief_url = ((resp.get('links') or {}).get('next') or {}).get('href')
        return results, total_count
