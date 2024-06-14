import graphene

from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import Lead

LeadConfidentialityEnum = convert_enum_to_graphene_enum(Lead.Confidentiality, name="LeadConfidentialityEnum")
LeadStatusEnum = convert_enum_to_graphene_enum(Lead.Status, name="LeadStatusEnum")
LeadPriorityEnum = convert_enum_to_graphene_enum(Lead.Priority, name="LeadPriorityEnum")
LeadSourceTypeEnum = convert_enum_to_graphene_enum(Lead.SourceType, name="LeadSourceTypeEnum")
LeadExtractionStatusEnum = convert_enum_to_graphene_enum(Lead.ExtractionStatus, name="LeadExtractionStatusEnum")
LeadAutoEntryExtractionTypeEnum = convert_enum_to_graphene_enum(Lead.AutoExtractionStatus, name="LeadAutoEntryExtractionTypeEnum")

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (Lead.confidentiality, LeadConfidentialityEnum),
        (Lead.status, LeadStatusEnum),
        (Lead.priority, LeadPriorityEnum),
        (Lead.source_type, LeadSourceTypeEnum),
        (Lead.extraction_status, LeadExtractionStatusEnum),
        (Lead.auto_entry_extraction_status, LeadAutoEntryExtractionTypeEnum),
    )
}


# TODO: Define this dynamically through a list?
class LeadOrderingEnum(graphene.Enum):
    # ASC
    ASC_ID = "id"
    ASC_CREATED_AT = "created_at"
    ASC_TITLE = "title"
    ASC_SOURCE = "source__title"
    ASC_PUBLISHED_ON = "published_on"
    ASC_CREATED_BY = "created_by"
    ASC_ASSIGNEE = "assignee__first_name"
    ASC_PRIORITY = "priority"
    # # Custom Filters
    ASC_PAGE_COUNT = "page_count"
    ASC_ENTRIES_COUNT = "entries_count"
    # DESC
    DESC_ID = f"-{ASC_ID}"
    DESC_CREATED_AT = f"-{ASC_CREATED_AT}"
    DESC_TITLE = f"-{ASC_TITLE}"
    DESC_SOURCE = f"-{ASC_SOURCE}"
    DESC_PUBLISHED_ON = f"-{ASC_PUBLISHED_ON}"
    DESC_CREATED_BY = f"-{ASC_CREATED_BY}"
    DESC_ASSIGNEE = f"-{ASC_ASSIGNEE}"
    DESC_PRIORITY = f"-{ASC_PRIORITY}"
    # # Custom Filters
    DESC_PAGE_COUNT = f"-{ASC_PAGE_COUNT}"
    DESC_ENTRIES_COUNT = f"-{ASC_ENTRIES_COUNT}"
