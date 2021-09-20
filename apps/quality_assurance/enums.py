from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from quality_assurance.models import CommentType, BaseReviewComment

ReviewCommentTypeEnum = convert_enum_to_graphene_enum(CommentType, name='ReviewCommentTypeEnum')

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (BaseReviewComment.comment_type, ReviewCommentTypeEnum),
    )
}
