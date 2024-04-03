import graphene

from django.db.models import QuerySet
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination
from entry.schema import EntryType
from lead.schema import LeadDetailType
from project.schema import ProjectDetailType

from utils.graphene.enums import EnumDescription
from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from deep.trackers import track_user

from lead.models import Lead
from entry.models import Entry
from .models import Assignment, Notification
from .filter_set import NotificationGqlFilterSet, AssignmentFilterSet
from .enums import (
    NotificationTypeEnum,
    NotificationStatusEnum,
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


class AssignmentType(DjangoObjectType):
    class Meta:
        model = Assignment

    project = graphene.Field(ProjectDetailType)
    content_type = graphene.String(required=False)
    object_id = graphene.ID(required=True)
    lead_type = graphene.Field(LeadDetailType)
    entry_type = graphene.Field(EntryType)

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_user_assignment_qs(info)

    @staticmethod
    def resolve_content_type(root, info):
        return root.content_type.model

    @staticmethod
    def resolve_lead_type(root, info):
        return Lead(root.object_id) if root.content_type.model == 'lead' else None

    @staticmethod
    def resolve_entry_type(root, info):
        return Entry(root.object_id) if root.content_type.model == 'entry' else None


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
