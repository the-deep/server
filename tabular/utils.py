import random
from datetime import datetime
from dateparser import parse as dateparse
from geo.models import GeoArea

from utils.common import calculate_sample_size, get_max_occurence_and_count


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
    except (ValueError, TypeError):
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
            "id": x.id,
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


def sample_and_detect_type_and_options(values, geos_names={}, geos_codes={}):
    # Importing here coz this is util and might be imported in models
    from .models import Field  # noqa

    length = len(values)
    sample_size = calculate_sample_size(length, 95, prob=0.8)

    samples = random.sample(values, round(sample_size))

    geo_parsed = None

    types = []
    geo_options = []
    date_options = []

    for sample in samples:
        number_parsed = parse_number(sample)
        if number_parsed:
            types.append(Field.NUMBER)
            continue

        datetime_parsed = auto_detect_datetime(sample)
        if datetime_parsed:
            types.append(Field.DATETIME)
            date_options.append({'date_format': datetime_parsed[1]})
            continue

        geo_parsed = parse_geo(sample, geos_names, geos_codes)
        if geo_parsed is not None:
            types.append(Field.GEO)
            geo_options.append({
                'geo_type': geo_parsed['geo_type'],
                'admin_level': geo_parsed['admin_level'],
            })
            continue
        types.append(Field.STRING)

    max_type, max_options = Field.STRING, {}

    # Find dominant type
    max_type, max_count = get_max_occurence_and_count(types)

    # Now find dominant option value
    if max_type == Field.DATETIME:
        max_format, max_count = get_max_occurence_and_count([
            x['date_format'] for x in date_options
        ])
        max_options = {
            'date_format': max_format
        }
    elif max_type == Field.GEO:
        max_geo, max_count = get_max_occurence_and_count([
            x['geo_type'] for x in geo_options
        ])
        max_admin, max_count = get_max_occurence_and_count([
            x['admin_level'] for x in geo_options
        ])
        max_options = {
            'geo_type': max_geo,
            'admin_level': max_admin
        }
    return {
        'type': max_type,
        'options': max_options
    }
