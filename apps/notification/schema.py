import graphene

from django.db.models import QuerySet
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.enums import EnumDescription
from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField

from .models import Notification
from .filter_set import NotificationGqlFilterSet
from .enums import (
    NotificationTypeEnum,
    NotificationStatusEnum,
)


def get_user_notification_qs(info):
    return Notification.objects.filter(
        receiver=info.context.request.user,
    )


class NotificationType(DjangoObjectType):
    class Meta:
        model = Notification
        fields = (
            'id', 'project', 'data', 'timestamp',
        )

    notification_type = graphene.Field(graphene.NonNull(NotificationTypeEnum))
    notification_type_display = EnumDescription(source='get_notification_type_display', required=True)
    status = graphene.Field(graphene.NonNull(NotificationStatusEnum))
    status_display = EnumDescription(source='get_status_display', required=True)

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_user_notification_qs(info)


class NotificationListType(CustomDjangoListObjectType):
    class Meta:
        model = Notification
        filterset_class = NotificationGqlFilterSet


class Query:
    notification = DjangoObjectField(NotificationType)
    notifications = DjangoPaginatedListObjectField(
        NotificationListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def resolve_notifications(root, info, **kwargs) -> QuerySet:
        return get_user_notification_qs(info)
