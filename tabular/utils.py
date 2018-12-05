from dateparser import parse as dateparse
from geo.models import GeoArea


def parse_number(val):
    try:
        float(val)
        return True
    except ValueError:
        return False


def parse_datetime(val):
    # try date parsing for english, french and spanish languages only
    date = dateparse(val, languages=['en', 'fr', 'es'])
    return date is not None


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
