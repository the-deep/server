import graphene

from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import NoOrderingPageGraphqlPagination
from utils.graphene.enums import EnumDescription
from deep.permissions import ProjectPermissions as PP
from lead.models import Lead

from quality_assurance.models import EntryReviewComment, EntryReviewCommentText
from .enums import EntryReviewCommentTypeEnum
from .filters import EntryReviewCommentGQFilterSet


def get_entry_comment_qs(info):
    """
    NOTE: To be used in EntryReviewCommentDetailType
    """
    entry_comment_qs = EntryReviewComment.objects.filter(
        entry__project=info.context.active_project
    )
    # Generate queryset according to permission
    if PP.check_permission(info, PP.Permission.VIEW_ENTRY):
        if PP.check_permission(info, PP.Permission.VIEW_ALL_LEAD):
            return entry_comment_qs
        elif PP.check_permission(info, PP.Permission.VIEW_ONLY_UNPROTECTED_LEAD):
            return entry_comment_qs.filter(entry__lead__confidentiality=Lead.Confidentiality.UNPROTECTED)
    return EntryReviewComment.objects.none()


class EntryReviewCommentTextType(DjangoObjectType):
    class Meta:
        model = EntryReviewCommentText
        only_fields = (
            'id',
            'created_at',
            'text',
        )


class EntryReviewCommentType(DjangoObjectType):
    class Meta:
        model = EntryReviewComment
        only_fields = (
            'id',
            'created_by',
            'created_at',
            'mentioned_users'
        )

    comment_type = graphene.Field(EntryReviewCommentTypeEnum, required=True)
    comment_type_display = EnumDescription(source='get_comment_type_display', required=True)
    text = graphene.String()
    entry = graphene.ID(source='entry_id', required=True)


class EntryReviewCommentDetailType(EntryReviewCommentType):
    class Meta:
        model = EntryReviewComment
        skip_registry = True
        only_fields = (
            'id',
            'entry',
            'created_by',
            'created_at',
            'mentioned_users'
        )

    text_history = graphene.List(graphene.NonNull(EntryReviewCommentTextType))

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_entry_comment_qs(info)

    @staticmethod
    def resolve_text_history(root, info, **kwargs):
        return info.context.dl.quality_assurance.text_history.load(root.pk)


class EntryReviewCommentListType(CustomDjangoListObjectType):
    class Meta:
        model = EntryReviewComment
        filterset_class = EntryReviewCommentGQFilterSet


class Query:
    review_comment = DjangoObjectField(EntryReviewCommentDetailType)
    review_comments = DjangoPaginatedListObjectField(
        EntryReviewCommentListType,
        pagination=NoOrderingPageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def resolve_review_comments(root, info, **kwargs):
        return get_entry_comment_qs(info)
