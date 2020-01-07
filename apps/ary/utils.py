from geo.models import Region, GeoArea
from organization.models import Organization

from utils.common import parse_number


def get_title_or_none(Model):
    def _get_title(val):
        instance = Model.objects.filter(id=val).first()
        return instance and instance.title
    return _get_title


def get_location_title(val):
    if isinstance(val, dict):
        return val.get('geo_json') and \
            val['geo_json'].get('properties') and \
            val['geo_json']['properties'].get('title')
    instance = GeoArea.objects.filter(id=val).first()
    return instance and instance.title

def get_model_attr_or_none(Model, attr):
    def _get_attr(val):
        instance = Model.objects.filter(id=val).first()
        return instance and instance.__dict__.get(attr)
    return _get_attr


def get_model_attrs_or_empty_dict(Model, attrs=[]):
    def _get_attrs(val):
        instance = Model.objects.filter(id=val).first()
        if not instance:
            return {attr: None for attr in attrs}
        return {attr: instance.__dict__.get(attr) for attr in attrs}
    return _get_attrs


def get_country_name(cid):
    region = Region.objects.filter(id=parse_number(cid)).first()
    return region and region.title


def get_organization_name(did):
    org = Organization.objects.filter(id=parse_number(did)).first()
    if org:
        m_org = org.data
        return {
            'name': m_org.title,
            'type': m_org.organization_type and m_org.organization_type.title,
            'key': did,
        }
    return {
        'name': '',
        'type': '',
        'key': did,
    }


FIELDS_KEYS_VALUE_EXTRACTORS = {
    'Country': get_country_name,
    'Donor': get_organization_name,
    'Partner': get_organization_name,
    'Partners': get_organization_name,
    'Lead Organization': get_organization_name,
    'International Partners': get_organization_name,
    'Government': get_organization_name,
    'National Partners': get_organization_name,
}
