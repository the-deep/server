from geo.models import Region
from organization.models import Organization

from utils.common import parse_number


def get_country_name(cid):
    region = Region.objects.filter(id=parse_number(cid)).first()
    return region and region.title


def get_organization_name(did):
    org = Organization.objects.filter(id=parse_number(did)).first()
    return {
        'name': org.title,
        'type': org.organization_type and org.organization_type.title,
        'key': did,
    } if org else {}


FIELDS_KEYS_VALUE_EXTRACTORS = {
    'Country': get_country_name,
    'Donor': get_organization_name,
    'Partner': get_organization_name,
    'Partners': get_organization_name,
    'Lead Organization': get_organization_name,
}
