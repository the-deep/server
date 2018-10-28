from dateparser import parse as dateparse
from geo.models import GeoArea


def parse_number(val):
    try:
        float(val)
        return True
    except ValueError as ve:
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
    return {x.title.lower(): True for x in geos}


def parse_geo(value, geos={}):
    return geos.get(value.lower()) is not None
