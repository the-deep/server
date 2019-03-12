import re
import random
from datetime import datetime
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
    '%Y-%b-%d',  # 2019-Jan-12
    '%Y/%b/%d',  # 2019/Jan/12
    '%Y %B %d',  # 2019 January 12
    '%Y-%B-%d',  # 2019-January-12
    '%d %B %Y',  # 12 January 2019

    '%d-%m-%Y',
    '%d/%m/%Y',
    '%d.%m.%Y',
    '%d %m %Y',
]

COMMA_SEPARATED_NUMBER = re.compile(r'^(\d{1,3})(,\d{3})*(\.\d+)?$')
SPACE_SEPARATED_NUMBER = re.compile(r'^(\d{1,3})( \d{3})*(\.\d+)?$')
DOT_SEPARATED_NUMBER = re.compile(r'^(\d{1,3})(\.\d{3})*(,\d+)?$')


def parse_number(val, **kwargs):
    val = str(val)
    separator = kwargs.get('separator')
    if separator == 'comma':
        return parse_comma_separated(val)
    elif separator == 'dot':
        return parse_dot_separated(val)
    elif separator == 'space':
        return parse_space_separated(val)
    elif separator == 'none':
        return parse_none_separated(val)
    elif separator is None:
        return parse_no_separator(val)


def parse_no_separator(val):
    return (
        parse_none_separated(val) or
        parse_comma_separated(val) or
        parse_dot_separated(val) or
        parse_space_separated(val) or
        None
    )


def parse_none_separated(numstring):
    try:
        return float(numstring), 'none'
    except (TypeError, ValueError):
        return None


def parse_comma_separated(numstring):
    try:
        if not COMMA_SEPARATED_NUMBER.match(numstring.strip()):
            return None
        comma_removed = numstring.replace(',', '')
        return float(comma_removed), 'comma'
    except (ValueError, TypeError, AttributeError):
        # Attribute error is raised by numstring.replace if numstring is None
        return None


def parse_dot_separated(numstring):
    try:
        if not DOT_SEPARATED_NUMBER.match(numstring.strip()):
            return None
        # first, remove dot
        dot_removed = numstring.replace('.', '')
        # now replace comma with dot, to make it parseable
        comma_replaced = dot_removed.replace(',', '.')
        return float(comma_replaced), 'dot'
    except (ValueError, TypeError, AttributeError):
        # Attribute error is raised by numstring.replace if numstring is None
        return None


def parse_space_separated(numstring):
    try:
        if not SPACE_SEPARATED_NUMBER.match(numstring.strip()):
            return None
        # first, remove space
        space_removed = numstring.replace(' ', '')
        return float(space_removed), 'space'
    except (ValueError, TypeError, AttributeError):
        # Attribute error is raised by numstring.replace if numstring is None
        return None


def parse_string(val, **kwargs):
    # Just making it compatible to accept kwargs
    return str(val)


def parse_datetime(val, date_format=None, **kwargs):
    # Try date parsing for english, french and spanish languages only
    # The following parses numbers as well so if number matches, return None
    val = str(val)
    if not date_format and parse_number(val):
        return None

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
        return {}

    geos = GeoArea.objects.filter(
        admin_level__region__project=project
    ).values(
        'id', 'code', 'admin_level__level', 'title', 'admin_level_id',
        'admin_level__region', 'admin_level__region__title',
    )
    return {
        x['title'].lower(): {
            "admin_level": x['admin_level__level'],
            "admin_level_id": x['admin_level_id'],
            "title": x['title'],
            "code": x['code'],
            "id": x['id'],
            "region": x['admin_level__region'],
            "region_title": x['admin_level__region__title'],
        }
        for x in geos
    }


def parse_geo(value, geos_names={}, geos_codes={}, **kwargs):
    val = str(value).lower()
    name_match = geos_names.get(val)
    code_match = geos_codes.get(val)
    admin_level = kwargs.get('admin_level')
    # If admin_level is present, match admin_level as well

    parsed = None
    if name_match:
        parsed = {**name_match, 'geo_type': 'name'}
    elif code_match:
        parsed = {**code_match, 'geo_type': 'code'}
    else:
        return None

    if admin_level and admin_level != parsed['admin_level']:
        return None
    return parsed


def sample_and_detect_type_and_options(values, geos_names={}, geos_codes={}):
    # Importing here coz this is util and might be imported in models
    from .models import Field  # noqa

    if not values:
        return {
            'type': Field.STRING,
            'options': {}
        }

    length = len(values)
    sample_size = calculate_sample_size(length, 95, prob=0.8)

    samples = random.sample(values, round(sample_size))

    geo_parsed = None

    types = []
    geo_options = []
    date_options = []
    number_options = []

    for sample in samples:
        value = sample['value']
        number_parsed = parse_number(value)
        if number_parsed:
            types.append(Field.NUMBER)
            number_options.append(number_parsed[1])
            continue

        datetime_parsed = auto_detect_datetime(value)
        if datetime_parsed:
            types.append(Field.DATETIME)
            date_options.append({'date_format': datetime_parsed[1]})
            continue

        geo_parsed = parse_geo(value, geos_names, geos_codes)
        if geo_parsed is not None:
            types.append(Field.GEO)
            geo_options.append({
                'geo_type': geo_parsed['geo_type'],
                'admin_level': geo_parsed['admin_level'],
                'region': geo_parsed['region'],
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
        max_options = {'date_format': max_format}
    elif max_type == Field.NUMBER:
        max_format, max_count = get_max_occurence_and_count(number_options)
        max_options = {'separator': max_format}
    elif max_type == Field.GEO:
        max_options = get_geo_options(geo_options)

    return {
        'type': max_type,
        'options': max_options
    }


def get_cast_function(type, geos_names, geos_codes):
    from .models import Field
    if type == Field.STRING:
        cast_func = parse_string
    elif type == Field.NUMBER:
        cast_func = parse_number
    elif type == Field.DATETIME:
        cast_func = parse_datetime
    elif type == Field.GEO:
        cast_func = lambda v, **kwargs: parse_geo(v, geos_names, geos_codes, **kwargs)  # noqa
    return cast_func


def get_geo_options(geo_options):
    max_geo, max_count = get_max_occurence_and_count([
        x['geo_type'] for x in geo_options
    ])
    max_admin, max_count = get_max_occurence_and_count([
        x['admin_level'] for x in geo_options
    ])

    max_region, max_count = get_max_occurence_and_count([
        x['region'] for x in geo_options
    ])
    return {
        'geo_type': max_geo,
        'region': max_region,
        'admin_level': max_admin
    }
