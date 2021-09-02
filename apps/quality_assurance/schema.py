import graphene

from graphene_django import DjangoObjectType

from quality_assurance.models import EntryReviewComment, EntryReviewCommentText
from .enums import CommentTypeEnum


class EntryReviewCommentTextType(DjangoObjectType):
    class Meta:
        model = EntryReviewCommentText
        field = (
            'text',
            'created_at',
            'id'
        )


class EntryReviewCommentType(DjangoObjectType):
    class Meta:
        model = EntryReviewComment
        fields = (
            'id',
            'entry',
            'created_by',
            'created_at',
            'mentioned_users'
        )

    comment_type = graphene.Field(CommentTypeEnum)
    text_history = graphene.List(graphene.NonNull(EntryReviewCommentTextType))

    @staticmethod
    def resolve_text_history(root, info, **kwargs):
        return info.context.dl.quality_assurance.text_history.load(root.pk)
