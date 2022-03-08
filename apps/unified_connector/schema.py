import graphene
import datetime
from django.db.models import QuerySet
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField

from utils.graphene.enums import EnumDescription
from utils.graphene.pagination import NoOrderingPageGraphqlPagination
from utils.graphene.types import CustomDjangoListObjectType, ClientIdMixin
from utils.graphene.fields import DjangoPaginatedListObjectField
from user_resource.schema import UserResourceMixin
from deep.permissions import ProjectPermissions as PP

from .filters import (
    ConnectorSourceGQFilterSet,
    ConnectorSourceLeadGQFilterSet,
    UnifiedConnectorGQFilterSet,
)
from .models import (
    UnifiedConnector,
    ConnectorLead,
    ConnectorSource,
    ConnectorSourceLead,
)
from .enums import (
    ConnectorSourceSourceEnum,
    ConnectorSourceStatusEnum,
    ConnectorLeadExtractionStatusEnum,
)


def get_unified_connector_qs(info):
    qs = UnifiedConnector.objects.filter(project=info.context.active_project)
    if PP.check_permission(info, PP.Permission.VIEW_UNIFIED_CONNECTOR):
        return qs
    return qs.none()


def get_connector_source_qs(info):
    qs = ConnectorSource.objects.filter(unified_connector__project=info.context.active_project)
    if PP.check_permission(info, PP.Permission.VIEW_UNIFIED_CONNECTOR):
        return qs
    return qs.none()


def get_connector_source_lead_qs(info):
    qs = ConnectorSourceLead.objects.filter(source__unified_connector__project=info.context.active_project)
    if PP.check_permission(info, PP.Permission.VIEW_UNIFIED_CONNECTOR):
        return qs
    return qs.none()


# NOTE: This is not used directly
class ConnectorLeadType(DjangoObjectType):
    extraction_status = graphene.Field(ConnectorLeadExtractionStatusEnum, required=True)
    extraction_status_display = EnumDescription(source='get_extraction_status_display', required=True)

    class Meta:
        model = ConnectorLead
        fields = (
            'id',
            'url',
            'title',
            'published_on',
            'source_raw',
            'author_raw',
            'source',  # TODO: Dataloader
            'authors',  # TODO: Dataloader
        )


class ConnectorSourceLeadType(DjangoObjectType):
    connector_lead = graphene.Field(ConnectorLeadType, required=True)  # TODO: Dataloader
    source = graphene.ID(required=True, source='source_id')

    class Meta:
        model = ConnectorSourceLead
        fields = (
            'id',
            'blocked',
            'already_added',
        )

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_connector_source_lead_qs(info)


class ConnectorSourceLeadListType(CustomDjangoListObjectType):
    class Meta:
        model = ConnectorSourceLead
        filterset_class = ConnectorSourceLeadGQFilterSet


class ConnectorSourceStatsType(graphene.ObjectType):
    date = graphene.Date(required=True)
    count = graphene.Int(required=True)

    @staticmethod
    def resolve_date(root, info, **kwargs):
        return datetime.datetime.strptime(root['date'], '%Y-%m-%d')


class ConnectorSourceType(UserResourceMixin, ClientIdMixin, DjangoObjectType):
    source = graphene.Field(ConnectorSourceSourceEnum, required=True)
    source_display = EnumDescription(source='get_source_display', required=True)
    unified_connector = graphene.ID(required=True, source='unified_connector_id')
    stats = graphene.List(ConnectorSourceStatsType)
    leads_count = graphene.Int(required=True)
    status = graphene.Field(ConnectorSourceStatusEnum, required=True)
    status_display = EnumDescription(source='get_status_display', required=True)

    class Meta:
        model = ConnectorSource
        fields = (
            'id',
            'title',
            'unified_connector',
            'last_fetched_at',
            'params',
        )

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_connector_source_qs(info)

    @staticmethod
    def resolve_stats(root, info, **kwargs):
        return (root.stats or {}).get('published_dates') or []

    @staticmethod
    def resolve_leads_count(root, info, **kwargs):  # FIXME: Load real-time?
        return (root.stats or {}).get('leads_count') or 0


class ConnectorSourceListType(CustomDjangoListObjectType):
    class Meta:
        model = ConnectorSource
        filterset_class = ConnectorSourceGQFilterSet


class UnifiedConnectorType(UserResourceMixin, ClientIdMixin, DjangoObjectType):
    project = graphene.ID(required=True, source='project_id')
    sources = graphene.List(graphene.NonNull(ConnectorSourceType))
    leads_count = graphene.Int(required=True)

    class Meta:
        model = UnifiedConnector
        fields = (
            'id',
            'title',
            'is_active',
        )

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_unified_connector_qs(info)

    @staticmethod
    def resolve_leads_count(root, info, **kwargs):
        return ConnectorSourceLead.objects.filter(
            source__unified_connector=root,
        ).distinct().count()  # TODO: Dataloader

    @staticmethod
    def resolve_sources(root, info, **kwargs):
        return root.sources.order_by('id')  # TODO: Dataloader


class UnifiedConnectorListType(CustomDjangoListObjectType):
    class Meta:
        model = UnifiedConnector
        filterset_class = UnifiedConnectorGQFilterSet


# This is attached to project type.
class UnifiedConnectorQueryType(graphene.ObjectType):
    unified_connector = DjangoObjectField(UnifiedConnectorType)
    unified_connectors = DjangoPaginatedListObjectField(
        UnifiedConnectorListType,
        pagination=NoOrderingPageGraphqlPagination(
            page_size_query_param='pageSize',
        )
    )
    connector_source = DjangoObjectField(ConnectorSourceType)
    connector_sources = DjangoPaginatedListObjectField(
        ConnectorSourceListType,
        pagination=NoOrderingPageGraphqlPagination(
            page_size_query_param='pageSize',
        )
    )
    connector_source_lead = DjangoObjectField(ConnectorSourceLeadType)
    connector_source_leads = DjangoPaginatedListObjectField(
        ConnectorSourceLeadListType,
        pagination=NoOrderingPageGraphqlPagination(
            page_size_query_param='pageSize',
        )
    )

    @staticmethod
    def resolve_unified_connectors(root, info, **kwargs) -> QuerySet:
        return get_unified_connector_qs(info)

    @staticmethod
    def resolve_connector_sources(root, info, **kwargs) -> QuerySet:
        return get_connector_source_qs(info)

    @staticmethod
    def resolve_connector_source_leads(root, info, **kwargs) -> QuerySet:
        return get_connector_source_lead_qs(info)
