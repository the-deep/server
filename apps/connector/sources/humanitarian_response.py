import logging
import requests
from bs4 import BeautifulSoup as Soup
from datetime import datetime

from .base import Source
from connector.utils import ConnectorWrapper
from lead.models import Lead

logger = logging.getLogger(__name__)


COUNTRIES_OPTIONS = [
    {"key": "afghanistan", "label": "Afghanistan"},
    {"key": "albania", "label": "Albania"},
    {"key": "angola", "label": "Angola"},
    {"key": "anguilla", "label": "Anguilla"},
    {"key": "antigua-and-barbuda", "label": "Antigua and Barbuda"},
    {"key": "argentina", "label": "Argentina"},
    {"key": "austria", "label": "Austria"},
    {"key": "bahamas", "label": "Bahamas"},
    {"key": "bangladesh", "label": "Bangladesh"},
    {"key": "barbados", "label": "Barbados"},
    {"key": "benin", "label": "Benin"},
    {"key": "bolivia-plurinational-state", "label": "Bolivia, Plurinational State of"},
    {"key": "bonaire-sint-eustatius-and-saba", "label": "Bonaire, Sint Eustatius and Saba"},
    {"key": "botswana", "label": "Botswana"},
    {"key": "brazil", "label": "Brazil"},
    {"key": "burkina-faso", "label": "Burkina Faso"},
    {"key": "burundi", "label": "Burundi"},
    {"key": "cape-verde", "label": "Cabo Verde"},
    {"key": "cambodia", "label": "Cambodia"},
    {"key": "cameroon", "label": "Cameroon"},
    {"key": "cayman-islands", "label": "Cayman Islands"},
    {"key": "central-african-republic", "label": "Central African Republic"},
    {"key": "chad", "label": "Chad"},
    {"key": "chile", "label": "Chile"},
    {"key": "colombia", "label": "Colombia"},
    {"key": "comoros", "label": "Comoros"},
    {"key": "congo", "label": "Congo"},
    {"key": "congo-democratic-republic", "label": "Congo, Democratic Republic of the"},
    {"key": "cook-islands", "label": "Cook Islands"},
    {"key": "costa-rica", "label": "Costa Rica"},
    {"key": "cuba", "label": "Cuba"},
    {"key": "côte-divoire", "label": "C\u00f4te d'Ivoire"},
    {"key": "korea-democratic-peoples-republic", "label": "Democratic People's Republic of Korea"},
    {"key": "djibouti", "label": "Djibouti"},
    {"key": "dominica", "label": "Dominica"},
    {"key": "dominican-republic", "label": "Dominican Republic"},
    {"key": "ecuador", "label": "Ecuador"},
    {"key": "egypt", "label": "Egypt"},
    {"key": "el-salvador", "label": "El Salvador"},
    {"key": "equatorial-guinea", "label": "Equatorial Guinea"},
    {"key": "eritrea", "label": "Eritrea"},
    {"key": "estonia", "label": "Estonia"},
    {"key": "swaziland", "label": "Eswatini"},
    {"key": "ethiopia", "label": "Ethiopia"},
    {"key": "fiji", "label": "Fiji"},
    {"key": "france", "label": "France"},
    {"key": "french-southern-territories", "label": "French Southern Territories"},
    {"key": "gabon", "label": "Gabon"},
    {"key": "gambia", "label": "Gambia"},
    {"key": "ghana", "label": "Ghana"},
    {"key": "grenada", "label": "Grenada"},
    {"key": "guadeloupe", "label": "Guadeloupe"},
    {"key": "guatemala", "label": "Guatemala"},
    {"key": "guinea", "label": "Guinea"},
    {"key": "guinea-bissau", "label": "Guinea-Bissau"},
    {"key": "guyana", "label": "Guyana"},
    {"key": "haiti", "label": "Haiti"},
    {"key": "honduras", "label": "Honduras"},
    {"key": "india", "label": "India"},
    {"key": "indonesia", "label": "Indonesia"},
    {"key": "iran-islamic-republic", "label": "Iran, Islamic Republic of"},
    {"key": "iraq", "label": "Iraq"},
    {"key": "jamaica", "label": "Jamaica"},
    {"key": "japan", "label": "Japan"},
    {"key": "jordan", "label": "Jordan"},
    {"key": "kenya", "label": "Kenya"},
    {"key": "kiribati", "label": "Kiribati"},
    {"key": "simulation-klanndestan", "label": "Klanndestan"},
    {"key": "kyrgyzstan", "label": "Kyrgyzstan"},
    {"key": "lao-peoples-democratic-republic", "label": "Lao People's Democratic Republic"},
    {"key": "lebanon", "label": "Lebanon"},
    {"key": "lesotho", "label": "Lesotho"},
    {"key": "liberia", "label": "Liberia"},
    {"key": "libya", "label": "Libya"},
    {"key": "madagascar", "label": "Madagascar"},
    {"key": "malawi", "label": "Malawi"},
    {"key": "mali", "label": "Mali"},
    {"key": "marshall-islands", "label": "Marshall Islands"},
    {"key": "martinique", "label": "Martinique"},
    {"key": "mauritania", "label": "Mauritania"},
    {"key": "mauritius", "label": "Mauritius"},
    {"key": "mexico", "label": "Mexico"},
    {"key": "micronesia-federated-states", "label": "Micronesia, Federated States of"},
    {"key": "mongolia", "label": "Mongolia"},
    {"key": "montserrat", "label": "Montserrat"},
    {"key": "mozambique", "label": "Mozambique"},
    {"key": "myanmar", "label": "Myanmar"},
    {"key": "namibia", "label": "Namibia"},
    {"key": "nauru", "label": "Nauru"},
    {"key": "nepal", "label": "Nepal"},
    {"key": "nicaragua", "label": "Nicaragua"},
    {"key": "niger", "label": "Niger"},
    {"key": "nigeria", "label": "Nigeria"},
    {"key": "niue", "label": "Niue"},
    {"key": "occupied-palestinian-territory", "label": "occupied Palestinian territory"},
    {"key": "pakistan", "label": "Pakistan"},
    {"key": "palau", "label": "Palau"},
    {"key": "panama", "label": "Panama"},
    {"key": "papua-new-guinea", "label": "Papua New Guinea"},
    {"key": "paraguay", "label": "Paraguay"},
    {"key": "peru", "label": "Peru"},
    {"key": "philippines", "label": "Philippines"},
    {"key": "puerto-rico", "label": "Puerto Rico"},
    {"key": "rwanda", "label": "Rwanda"},
    {"key": "saint-barthélemy", "label": "Saint Barth\u00e9lemy"},
    {"key": "saint-kitts-and-nevis", "label": "Saint Kitts and Nevis"},
    {"key": "saint-lucia", "label": "Saint Lucia"},
    {"key": "saint-martin-french-part", "label": "Saint Martin"},
    {"key": "saint-vincent-and-grenadines", "label": "Saint Vincent and the Grenadines"},
    {"key": "samoa", "label": "Samoa"},
    {"key": "senegal", "label": "Senegal"},
    {"key": "seychelles", "label": "Seychelles"},
    {"key": "sierra-leone", "label": "Sierra Leone"},
    {"key": "sint-maarten-dutch-part", "label": "Simland"},
    {"key": "solomon-islands", "label": "Solomon Islands"},
    {"key": "somalia", "label": "Somalia"},
    {"key": "south-africa", "label": "South Africa"},
    {"key": "south-sudan", "label": "South Sudan"},
    {"key": "sri-lanka", "label": "Sri Lanka"},
    {"key": "sudan", "label": "Sudan"},
    {"key": "switzerland", "label": "Switzerland"},
    {"key": "syrian-arab-republic", "label": "Syrian Arab Republic"},
    {"key": "são-tomé-and-príncipe", "label": "S\u00e3o Tom\u00e9 and Pr\u00edncipe"},
    {"key": "tajikistan", "label": "Tajikistan"},
    {"key": "tanzania-united-republic", "label": "Tanzania, United Republic of"},
    {"key": "thailand", "label": "Thailand"},
    {"key": "timor-leste", "label": "Timor-Leste"},
    {"key": "togo", "label": "Togo"},
    {"key": "tokelau", "label": "Tokelau"},
    {"key": "tonga", "label": "Tonga"},
    {"key": "trinidad-and-tobago", "label": "Trinidad and Tobago"},
    {"key": "tunisia", "label": "Tunisia"},
    {"key": "turkey", "label": "Turkey"},
    {"key": "turks-and-caicos-islands", "label": "Turks and Caicos Islands"},
    {"key": "tuvalu", "label": "Tuvalu"},
    {"key": "uganda", "label": "Uganda"},
    {"key": "ukraine", "label": "Ukraine"},
    {"key": "united-arab-emirates", "label": "United Arab Emirates"},
    {"key": "vanuatu", "label": "Vanuatu"},
    {"key": "venezuela-bolivarian-republic", "label": "Venezuela"},
    {"key": "virgin-islands-british", "label": "Virgin Islands, British"},
    {"key": "virgin-islands-us", "label": "Virgin Islands, U.S."},
    {"key": "western-sahara", "label": "Western Sahara"},
    {"key": "world", "label": "World"},
    {"key": "yemen", "label": "Yemen"},
    {"key": "zambia", "label": "Zambia"},
    {"key": "zimbabwe", "label": "Zimbabwe"}
]


@ConnectorWrapper
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

    def get_content(self, url, params):
        resp = requests.get(url, params={})
        return resp.text

    def fetch(self, params, offset=None, limit=None):
        results = []
        url = self.URL
        if params.get('country'):
            url = self.URL + '/locations/' + params['country']
        content = self.get_content(url, {})
        soup = Soup(content, 'html.parser')
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
                    'source_type': Lead.SourceType.WEBSITE
                }
                results.append(data)
            except Exception as e:
                logger.warning(
                    "Exception parsing humanitarian response connector: " +
                    str(e.args)
                )

        final_results = results[offset: offset + limit]
        return final_results, len(results)
