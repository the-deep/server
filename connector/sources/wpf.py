import requests
from bs4 import BeautifulSoup as Soup

from .base import Source
from lead.models import Lead

COUNTRIES_OPTIONS = [
    {"key": "All", "label": "Any"},
    {"key": "120", "label": "Afghanistan"},
    {"key": "100", "label": "Algeria"},
    {"key": "124", "label": "Angola"},
    {"key": "101", "label": "Armenia"},
    {"key": "102", "label": "Azerbaijan"},
    {"key": "133", "label": "Bangladesh"},
    {"key": "138", "label": "Benin"},
    {"key": "140", "label": "Bhutan"},
    {"key": "141", "label": "Bolivia"},
    {"key": "4790", "label": "Brazil"},
    {"key": "150", "label": "Burkina Faso"},
    {"key": "151", "label": "Burundi"},
    {"key": "152", "label": "Cambodia"},
    {"key": "153", "label": "Cameroon"},
    {"key": "155", "label": "Cape Verde"},
    {"key": "157", "label": "Central African Republic"},
    {"key": "111", "label": "Chad"},
    {"key": "3801", "label": "China"},
    {"key": "82", "label": "Colombia"},
    {"key": "162", "label": "Comoros"},
    {"key": "164", "label": "Congo"},
    {"key": "163", "label": "Congo, Democratic Republic of the"},
    {"key": "167", "label": "Côte d'Ivoire"},
    {"key": "169", "label": "Cuba"},
    {"key": "173", "label": "Djibouti"},
    {"key": "175", "label": "Dominican Republic"},
    {"key": "176", "label": "Ecuador"},
    {"key": "103", "label": "Egypt"},
    {"key": "177", "label": "El Salvador"},
    {"key": "179", "label": "Eritrea"},
    {"key": "314", "label": "Eswatini"},
    {"key": "181", "label": "Ethiopia"},
    {"key": "320", "label": "Gambia"},
    {"key": "191", "label": "Georgia"},
    {"key": "193", "label": "Ghana"},
    {"key": "200", "label": "Guatemala"},
    {"key": "201", "label": "Guinea"},
    {"key": "202", "label": "Guinea-Bissau"},
    {"key": "204", "label": "Haiti"},
    {"key": "207", "label": "Honduras"},
    {"key": "211", "label": "India"},
    {"key": "212", "label": "Indonesia"},
    {"key": "104", "label": "Iran"},
    {"key": "105", "label": "Iraq"},
    {"key": "3562", "label": "Japan"},
    {"key": "106", "label": "Jordan"},
    {"key": "3660", "label": "Kazakhstan"},
    {"key": "220", "label": "Kenya"},
    {"key": "222", "label": "Korea, Democratic People's Republic of"},
    {"key": "225", "label": "Kyrgyzstan"},
    {"key": "226", "label": "Lao People’s Democratic Republic"},
    {"key": "3439", "label": "Lebanon"},
    {"key": "229", "label": "Lesotho"},
    {"key": "230", "label": "Liberia"},
    {"key": "3544", "label": "Libya"},
    {"key": "237", "label": "Madagascar"},
    {"key": "238", "label": "Malawi"},
    {"key": "241", "label": "Mali"},
    {"key": "245", "label": "Mauritania"},
    {"key": "3646", "label": "Moldova, Republic of"},
    {"key": "3657", "label": "Morocco"},
    {"key": "256", "label": "Mozambique"},
    {"key": "257", "label": "Myanmar"},
    {"key": "258", "label": "Namibia"},
    {"key": "260", "label": "Nepal"},
    {"key": "265", "label": "Nicaragua"},
    {"key": "266", "label": "Niger"},
    {"key": "3659", "label": "Nigeria"},
    {"key": "273", "label": "Pakistan"},
    {"key": "107", "label": "Palestine, State of"},
    {"key": "275", "label": "Panama"},
    {"key": "434", "label": "Peru"},
    {"key": "279", "label": "Philippines"},
    {"key": "287", "label": "Russian Federation"},
    {"key": "288", "label": "Rwanda"},
    {"key": "296", "label": "Sao Tome and Principe"},
    {"key": "298", "label": "Senegal"},
    {"key": "302", "label": "Sierra Leone"},
    {"key": "307", "label": "Somalia"},
    {"key": "3647", "label": "South Africa"},
    {"key": "3652", "label": "South Sudan"},
    {"key": "311", "label": "Sri Lanka"},
    {"key": "112", "label": "Sudan"},
    {"key": "108", "label": "Syrian Arab Republic"},
    {"key": "109", "label": "Tajikistan"},
    {"key": "318", "label": "Tanzania, United Republic of"},
    {"key": "321", "label": "Timor-Leste"},
    {"key": "322", "label": "Togo"},
    {"key": "3779", "label": "Tunisia"},
    {"key": "5108", "label": "Turkey"},
    {"key": "332", "label": "Uganda"},
    {"key": "5071", "label": "Ukraine"},
    {"key": "3658", "label": "Uzbekistan"},
    {"key": "4791", "label": "Viet Nam"},
    {"key": "110", "label": "Yemen"},
    {"key": "345", "label": "Zambia"},
    {"key": "346", "label": "Zimbabwe"},
]

YEAR_OPTIONS = [
    {"key": "All", "label": "Any"},
    {"key": "421", "label": "1993"},
    {"key": "420", "label": "1994"},
    {"key": "377", "label": "1995"},
    {"key": "378", "label": "1996"},
    {"key": "379", "label": "1997"},
    {"key": "380", "label": "1998"},
    {"key": "381", "label": "1999"},
    {"key": "368", "label": "2000"},
    {"key": "369", "label": "2001"},
    {"key": "370", "label": "2002"},
    {"key": "371", "label": "2003"},
    {"key": "372", "label": "2004"},
    {"key": "373", "label": "2005"},
    {"key": "374", "label": "2006"},
    {"key": "375", "label": "2007"},
    {"key": "376", "label": "2008"},
    {"key": "1277", "label": "2009"},
    {"key": "2595", "label": "2010"},
    {"key": "3464", "label": "2011"},
    {"key": "3916", "label": "2012"},
    {"key": "4184", "label": "2013"},
    {"key": "4689", "label": "2014"},
    {"key": "5006", "label": "2015"},
    {"key": "5109", "label": "2016"},
    {"key": "5142", "label": "2017"},
    {"key": "5143", "label": "2018"},
]


class WorldFoodProgramme(Source):
    URL = 'https://www.wfp.org/food-security/assessment-bank'
    title = 'WFP Assessments'
    key = 'world-food-programme'
    options = [
        {
            'key': 'tid_1',
            'field_type': 'select',
            'title': 'Country',
            'options': COUNTRIES_OPTIONS
        },
        {
            'key': 'tid_6',
            'field_type': 'select',
            'title': 'Year',
            'options': YEAR_OPTIONS
        },
    ]

    def fetch(self, params, page=None, limit=None):
        results = []
        if page:
            params['page'] = page
        resp = requests.get(self.URL, params=params)

        soup = Soup(resp.text, 'html.parser')
        contents = soup.find('div', {'class': 'view-content'})
        if not contents:
            return results
        # iterate and get loops
        for row in contents.findAll('div', {'class': 'views-row'}):
            content = row.find('h3').find('a')
            title = content.get_text()
            url = content['href']
            data = Lead(
                title=title.strip(),
                url=url,
                source='WFP Assessments',
                website='www.wfp.org'
            )
            results.append(data)
        return results
