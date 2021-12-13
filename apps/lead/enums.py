import graphene

from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import Lead

LeadConfidentialityEnum = convert_enum_to_graphene_enum(Lead.Confidentiality, name='LeadConfidentialityEnum')
LeadStatusEnum = convert_enum_to_graphene_enum(Lead.Status, name='LeadStatusEnum')
LeadPriorityEnum = convert_enum_to_graphene_enum(Lead.Priority, name='LeadPriorityEnum')
LeadSourceTypeEnum = convert_enum_to_graphene_enum(Lead.SourceType, name='LeadSourceTypeEnum')
LeadExtractionStatusEnum = convert_enum_to_graphene_enum(Lead.ExtractionStatus, name='LeadExtractionStatusEnum')

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (Lead.confidentiality, LeadConfidentialityEnum),
        (Lead.status, LeadStatusEnum),
        (Lead.priority, LeadPriorityEnum),
        (Lead.source_type, LeadSourceTypeEnum),
        (Lead.extraction_status, LeadExtractionStatusEnum),
    )
}


# TODO: Define this dynamically through a list?
class LeadOrderingEnum(graphene.Enum):
    # ASC
    ASC_ID = 'id'
    ASC_CREATED_AT = 'created_at'
    ASC_TITLE = 'title'
    ASC_SOURCE = 'source'
    ASC_PUBLISHED_ON = 'published_on'
    ASC_CREATED_BY = 'created_by'
    ASC_ASSIGNEE = 'assignee'
    ASC_PRIORITY = 'priority'
    ASC_PAGE_COUNT = 'leadpreview__page_count'
    # DESC
    DESC_ID = '-id'
    DESC_CREATED_AT = '-created_at'
    DESC_TITLE = '-title'
    DESC_SOURCE = '-source'
    DESC_PUBLISHED_ON = '-published_on'
    DESC_CREATED_BY = '-created_by'
    DESC_ASSIGNEE = '-assignee'
    DESC_PRIORITY = '-priority'
    DESC_PAGE_COUNT = 'leadpreview__page_count'
