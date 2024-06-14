import graphene
from quality_assurance.models import EntryReviewComment

from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

EntryReviewCommentTypeEnum = convert_enum_to_graphene_enum(EntryReviewComment.CommentType, name="EntryReviewCommentTypeEnum")

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in ((EntryReviewComment.comment_type, EntryReviewCommentTypeEnum),)
}


class EntryReviewCommentOrderingEnum(graphene.Enum):
    # ASC
    ASC_ID = "id"
    ASC_CREATED_AT = "created_at"
    ASC_COMMENT_TYPE = "comment_type"
    ASC_ENTRY = "entry"
    # DESC
    DESC_ID = f"-{ASC_ID}"
    DESC_CREATED_AT = f"-{ASC_CREATED_AT}"
    DESC_COMMENT_TYPE = f"-{ASC_COMMENT_TYPE}"
    DESC_ENTRY = f"-{ASC_ENTRY}"
