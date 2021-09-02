__all__ = ['CommentTypeEnum']

import graphene

from quality_assurance.models import CommentType

from utils.graphene.enums import enum_description

CommentTypeEnum = graphene.Enum.from_enum(CommentType, description=enum_description)

enum_map = dict(
    COMMENT_TYPE=CommentTypeEnum
)
