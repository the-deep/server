import graphene

from django.db.models import QuerySet
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.enums import EnumDescription
from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from deep.trackers import track_user

from .models import Assignment, Notification
from .filter_set import NotificationGqlFilterSet, AssignmentFilterSet
from .enums import (
    NotificationTypeEnum,
    NotificationStatusEnum,
    AssignmentContentTypeEnum
)


def get_user_notification_qs(info):
    track_user(info.context.request.user.profile)
    return Notification.objects.filter(
        receiver=info.context.request.user,
    )


def get_user_assignment_qs(info):
    track_user(info.context.request.user.profile)
    return Assignment.get_for(track_user)


class NotificationType(DjangoObjectType):
    class Meta:
        model = Notification
        only_fields = (
            'id', 'project', 'data', 'timestamp',
        )

    notification_type = graphene.Field(graphene.NonNull(NotificationTypeEnum))
    notification_type_display = EnumDescription(source='get_notification_type_display', required=True)
    status = graphene.Field(graphene.NonNull(NotificationStatusEnum))
    status_display = EnumDescription(source='get_status_display', required=True)

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_user_notification_qs(info)


class AssignmentLeadDetailType(graphene.ObjectType):
    id = graphene.ID(required=True)
    title = graphene.String(required=True)


class AssignmentProjectDetailType(graphene.ObjectType):
    id = graphene.ID(required=True)
    title = graphene.String(required=True)


class AssignmentEntryReviewCommentDetailType(graphene.ObjectType):
    id = graphene.ID(required=True)
    entry_id = graphene.ID(required=True)
    lead_id = graphene.ID(required=True)


class AssignmentContentDataType(graphene.ObjectType):
    content_type = graphene.Field(AssignmentContentTypeEnum)
    lead = graphene.Field(AssignmentLeadDetailType)
    entry_review_comment = graphene.Field(AssignmentEntryReviewCommentDetailType)


class AssignmentType(DjangoObjectType):
    class Meta:
        model = Assignment
    id = graphene.ID(required=True)
    project = graphene.Field(AssignmentProjectDetailType)
    content_data = graphene.Field(AssignmentContentDataType)

    @staticmethod
    def resolve_content_data(root, info):
        return info.context.dl.notification.assignment.load(root.pk)


class NotificationListType(CustomDjangoListObjectType):
    class Meta:
        model = Notification
        filterset_class = NotificationGqlFilterSet


class AssignmentListType(CustomDjangoListObjectType):
    class Meta:
        model = Assignment
        filterset_class = AssignmentFilterSet


class Query:
    notification = DjangoObjectField(NotificationType)
    notifications = DjangoPaginatedListObjectField(
        NotificationListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
    assignments = DjangoPaginatedListObjectField(
        AssignmentListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def resolve_notifications(root, info, **kwargs) -> QuerySet:
        return get_user_notification_qs(info)

    @staticmethod
    def resolve_assignments(root, info, **kwargs) -> QuerySet:
        return Assignment.get_for(info.context.user)
