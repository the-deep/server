import graphene

from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import ConnectorSource, ConnectorLead

ConnectorSourceSourceEnum = convert_enum_to_graphene_enum(ConnectorSource.Source, name='ConnectorSourceSourceEnum')
ConnectorLeadExtractionStatusEnum = convert_enum_to_graphene_enum(
    ConnectorLead.ExtractionStatus, name='ConnectorLeadExtractionStatusEnum')
ConnectorSourceStatusEnum = convert_enum_to_graphene_enum(ConnectorSource.Status, name='ConnectorSourceStatusEnum')

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (ConnectorSource.source, ConnectorSourceSourceEnum),
        (ConnectorSource.status, ConnectorSourceStatusEnum),
        (ConnectorLead.extraction_status, ConnectorLeadExtractionStatusEnum),
    )
}


class UnifiedConnectorOrderingEnum(graphene.Enum):
    # ASC
    ASC_ID = 'id'
    ASC_CREATED_AT = 'created_at'
    ASC_TITLE = 'title'
    # DESC
    DESC_ID = f'-{ASC_ID}'
    DESC_CREATED_AT = f'-{ASC_CREATED_AT}'
    DESC_TITLE = f'-{ASC_TITLE}'


class ConnectorSourceOrderingEnum(graphene.Enum):
    # ASC
    ASC_ID = 'id'
    ASC_CREATED_AT = 'created_at'
    ASC_TITLE = 'title'
    ASC_SOURCE = 'source'
    # DESC
    DESC_ID = f'-{ASC_ID}'
    DESC_CREATED_AT = f'-{ASC_CREATED_AT}'
    DESC_TITLE = f'-{ASC_TITLE}'
    DESC_SOURCE = f'-{ASC_SOURCE}'


class ConnectorSourceLeadOrderingEnum(graphene.Enum):
    # ASC
    ASC_ID = 'id'
    ASC_LEAD_CREATED_AT = 'connector_lead__created_at'
    ASC_LEAD_TITLE = 'connector_lead__title'
    # DESC
    DESC_ID = f'-{ASC_ID}'
    DESC_LEAD_CREATED_AT = f'-{ASC_LEAD_CREATED_AT}'
    DESC_LEAD_TITLE = f'-{ASC_LEAD_TITLE}'
