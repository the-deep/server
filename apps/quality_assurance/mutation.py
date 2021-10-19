import graphene

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
)
from deep.permissions import ProjectPermissions as PP

from .models import EntryReviewComment
from .schema import EntryReviewCommentDetailType
from .serializers import (
    EntryReviewCommentGqlSerializer as EntryReviewCommentSerializer,
)


EntryReviewCommentInputType = generate_input_type_for_serializer(
    'EntryReviewCommentInputType',
    serializer_class=EntryReviewCommentSerializer,
)


class EntryReviewCommentMutationMixin():
    @classmethod
    def filter_queryset(cls, qs, info):
        return qs.filter(created_by=info.context.user)


class CreateEntryReviewComment(EntryReviewCommentMutationMixin, PsGrapheneMutation):
    class Arguments:
        data = EntryReviewCommentInputType(required=True)
    model = EntryReviewComment
    serializer_class = EntryReviewCommentSerializer
    result = graphene.Field(EntryReviewCommentDetailType)
    permissions = [PP.Permission.CREATE_ENTRY, PP.Permission.UPDATE_ENTRY]


class UpdateEntryReviewComment(EntryReviewCommentMutationMixin, PsGrapheneMutation):
    class Arguments:
        data = EntryReviewCommentInputType(required=True)
        id = graphene.ID(required=True)
    model = EntryReviewComment
    serializer_class = EntryReviewCommentSerializer
    result = graphene.Field(EntryReviewCommentDetailType)
    permissions = [PP.Permission.CREATE_ENTRY, PP.Permission.UPDATE_ENTRY]


class Mutation():
    entry_review_comment_create = CreateEntryReviewComment.Field()
    entry_review_comment_update = UpdateEntryReviewComment.Field()
