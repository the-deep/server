from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from quality_assurance.models import EntryReviewComment

EntryReviewCommentTypeEnum = convert_enum_to_graphene_enum(EntryReviewComment.CommentType, name='EntryReviewCommentTypeEnum')

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (EntryReviewComment.comment_type, EntryReviewCommentTypeEnum),
    )
}
