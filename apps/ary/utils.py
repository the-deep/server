from geo.models import Region
from organization.models import Organization


def get_country_name(cid):
    region = Region.objects.filter(id=cid).first()
    return region and region.title


def get_organization_name(did):
    org = Organization.objects.filter(id=did).first()
    return org and org.title


FIELDS_KEYS_VALUE_EXTRACTORS = {
    'Country': get_country_name,
    'Donor': get_organization_name,
    'Partner': get_organization_name,
    'Partners': get_organization_name,
}
