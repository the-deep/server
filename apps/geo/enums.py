import graphene


class GeoAreaOrderingEnum(graphene.Enum):
    # ASC
    ASC_ID = 'id'
    ASC_ADMIN_LEVEL = 'admin_level__level'
    # DESC
    DESC_ID = f'-{ASC_ID}'
    DESC_ADMIN_LEVEL = f'-{ASC_ADMIN_LEVEL}'
