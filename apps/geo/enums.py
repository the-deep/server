import graphene
from geo.models import Region

from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)


class GeoAreaOrderingEnum(graphene.Enum):
    # ASC
    ASC_ID = 'id'
    ASC_ADMIN_LEVEL = 'admin_level__level'
    # DESC
    DESC_ID = f'-{ASC_ID}'
    DESC_ADMIN_LEVEL = f'-{ASC_ADMIN_LEVEL}'


RegionStatusEnum = convert_enum_to_graphene_enum(
    Region.Status, name='RegionStatusEnum'
)


enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (Region.status, RegionStatusEnum),
    )
}
