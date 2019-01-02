from dateparser import parse as dateparse
from geo.models import GeoArea


def parse_number(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def parse_datetime(val):
    # Try date parsing for english, french and spanish languages only
    # The following parses numbers as well so if number matches, return None
    if parse_number(val):
        return None
    date = dateparse(val, languages=['en', 'fr', 'es'])
    return date


def get_geos_dict(project=None):
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


def parse_geo(value, geos_names={}, geos_codes={}):
    val = value.lower()
    name_match = geos_names.get(val)
    if name_match:
        return {**name_match, 'geo_type': 'name'}
    code_match = geos_codes.get(val)
    if code_match:
        return {**code_match, 'geo_type': 'code'}
    return None
