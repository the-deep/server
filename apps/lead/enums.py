from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import Lead

LeadConfidentialityEnum = convert_enum_to_graphene_enum(Lead.Confidentiality, name='LeadConfidentialityEnum')
LeadStatusEnum = convert_enum_to_graphene_enum(Lead.Status, name='LeadStatusEnum')
LeadPriorityEnum = convert_enum_to_graphene_enum(Lead.Priority, name='LeadPriorityEnum')
LeadSourceTypeEnum = convert_enum_to_graphene_enum(Lead.SourceType, name='LeadSourceTypeEnum')

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (Lead.confidentiality, LeadConfidentialityEnum),
        (Lead.status, LeadStatusEnum),
        (Lead.priority, LeadPriorityEnum),
        (Lead.source_type, LeadSourceTypeEnum),
    )
}
