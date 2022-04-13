import graphene


class OrganizationOrderingEnum(graphene.Enum):
    # ASC
    ASC_ID = 'id'
    ASC_CREATED_AT = 'created_at'
    ASC_TITLE = 'title'
    ASC_SHORT_NAME = 'short_name'
    ASC_LONG_NAME = 'long_name'
    ASC_ORGANIZATION_TYPE = 'organization_type__title'
    # DESC
    DESC_ID = f'-{ASC_ID}'
    DESC_CREATED_AT = f'-{ASC_CREATED_AT}'
    DESC_TITLE = f'-{ASC_TITLE}'
    DESC_SHORT_NAME = f'-{ASC_SHORT_NAME}'
    DESC_LONG_NAME = f'-{ASC_LONG_NAME}'
    DESC_ORGANIZATION_TYPE = f'-{ASC_ORGANIZATION_TYPE}'
    # Custom annotate fields
    ASC_TITLE_LENGTH = 'title_length'
    DESC_TITLE_LENGTH = f'-{ASC_TITLE_LENGTH}'
