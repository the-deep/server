import graphene

from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)
from lead.models import Lead
from quality_assurance.models import EntryReviewComment
from .models import Notification

NotificationTypeEnum = convert_enum_to_graphene_enum(Notification.Type, name='NotificationTypeEnum')
NotificationStatusEnum = convert_enum_to_graphene_enum(Notification.Status, name='NotificationStatusEnum')

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (Notification.notification_type, NotificationTypeEnum),
        (Notification.status, NotificationStatusEnum),
    )
}


class AssignmentContentTypeEnum(graphene.Enum):
    LEAD = Lead._meta.model_name
    ENTRY_REVIEW_COMMENT = EntryReviewComment._meta.model_name
