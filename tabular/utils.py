from datetime import datetime
from dateparser import parse as dateparse
from geo.models import GeoArea


DATE_FORMATS = [
    '%m-%d-%Y',
    '%m/%d/%Y',
    '%m.%d.%Y',
    '%m %d %Y',

    '%Y-%m-%d',
    '%Y/%m/%d',
    '%Y.%m.%d',
    '%Y %m %d',

    '%d %b %Y',  # 12 Jan 2019
    '%d-%b-%Y',
    '%d/%b/%Y',
    '%d.%b.%Y',

    '%Y %b %d',  # 2019 Jan 12
    '%Y %B %d',  # 2019 January 12
    '%d %B %Y',  # 12 January 2019

    '%d-%m-%Y',
    '%d/%m/%Y',
    '%d.%m.%Y',
    '%d %m %Y',
]


def parse_number(val, **kwargs):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def parse_string(val, **kwargs):
    # Just making it compatible to accept kwargs
    return str(val)


def parse_datetime(val, date_format=None, **kwargs):
    # Try date parsing for english, french and spanish languages only
    # The following parses numbers as well so if number matches, return None
    if not format and parse_number(val):
        return None
    elif not format:
        return dateparse(val, languages=['en', 'fr', 'es'])

    try:
        return datetime.strptime(val, date_format)
    except ValueError:
        return None


def auto_detect_datetime(val):
    for format in DATE_FORMATS:
        parsed = parse_datetime(val, format)
        if parsed:
            return parsed, format
    return None


def get_geos_dict(project=None, **kwargs):
    if project is None:
        geos = GeoArea.objects.all()
    else:
        geos = GeoArea.objects.filter(
            admin_level__region__project=project
        )
    return {
        x.title.lower(): {
            "admin_level": x.admin_level.id,
            "title": x.title,
            "code": x.code,
        }
        for x in geos
    }


def parse_geo(value, geos_names={}, geos_codes={}, **kwargs):
    val = value.lower()
    name_match = geos_names.get(val)
    if name_match:
        return {**name_match, 'geo_type': 'name'}
    code_match = geos_codes.get(val)
    if code_match:
        return {**code_match, 'geo_type': 'code'}
    return None
