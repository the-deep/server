import graphene
import datetime
from django.db.models import QuerySet, Q
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField

from utils.graphene.enums import EnumDescription
from utils.graphene.pagination import NoOrderingPageGraphqlPagination
from utils.graphene.types import CustomDjangoListObjectType, ClientIdMixin
from utils.graphene.fields import DjangoPaginatedListObjectField
from user_resource.schema import UserResourceMixin
from deep.permissions import ProjectPermissions as PP
from unified_connector.sources.rss_feed import RssFeed
from unified_connector.sources.atom_feed import AtomFeed

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
        only_fields = (
            'id',
            'url',
            'website',
            'title',
            'published_on',
            'source_raw',
            'author_raw',
            'source',
            'authors',
        )

    @staticmethod
    def resolve_url(root, info, **_):
        print('the root title is', root.url.split('amazonaws.com/')[-1])
        pdf_url = root.url.split('amazonaws.com/')[-1]
        csv_url = pdf_url.replace('pdf', 'csv')
        return {"pdf": get_presigned_url(pdf_url), "csv":get_presigned_url(csv_url)} if root.source.title=="KoboToolbox" else root.url

    @staticmethod
    def resolve_source(root, info, **_):

        return root.source_id and info.context.dl.unified_connector.connector_lead_source.load(root.source_id)

    @staticmethod
    def resolve_authors(root, info, **_):

        return info.context.dl.unified_connector.connector_lead_authors.load(root.pk)


class ConnectorSourceLeadType(DjangoObjectType):
    connector_lead = graphene.Field(ConnectorLeadType, required=True)
    source = graphene.ID(required=True, source='source_id')

    class Meta:
        model = ConnectorSourceLead
        only_fields = (
            'id',
            'blocked',
            'already_added',
        )


    @staticmethod
    def get_custom_queryset(queryset, info, **_):
        return get_connector_source_lead_qs(info)

    @staticmethod
    def resolve_connector_lead(root, info, **_):
        return info.context.dl.unified_connector.connector_source_lead_lead.load(root.connector_lead_id)


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


class ConnectorSourceLeadCountType(graphene.ObjectType):
    total = graphene.Int(required=True)
    blocked = graphene.Int(required=True)
    already_added = graphene.Int(required=True)


class ConnectorSourceType(UserResourceMixin, ClientIdMixin, DjangoObjectType):
    source = graphene.Field(ConnectorSourceSourceEnum, required=True)
    source_display = EnumDescription(source='get_source_display', required=True)
    unified_connector = graphene.ID(required=True, source='unified_connector_id')
    stats = graphene.List(ConnectorSourceStatsType)
    leads_count = graphene.NonNull(ConnectorSourceLeadCountType)
    status = graphene.Field(ConnectorSourceStatusEnum, required=True)
    status_display = EnumDescription(source='get_status_display', required=True)

    class Meta:
        model = ConnectorSource
        only_fields = (
            'id',
            'title',
            'unified_connector',
            'last_fetched_at',
            'params',
        )

    @staticmethod
    def get_custom_queryset(queryset, info, **_):

        return get_connector_source_qs(info)

    @staticmethod
    def resolve_stats(root, info, **_):

        return (root.stats or {}).get('published_dates') or []

    @staticmethod
    def resolve_leads_count(root, info, **_):

        return info.context.dl.unified_connector.connector_source_leads_count.load(root.pk)


class ConnectorSourceListType(CustomDjangoListObjectType):
    class Meta:
        model = ConnectorSource
        filterset_class = ConnectorSourceGQFilterSet


class UnifiedConnectorType(UserResourceMixin, ClientIdMixin, DjangoObjectType):
    project = graphene.ID(required=True, source='project_id')
    sources = graphene.List(graphene.NonNull(ConnectorSourceType))
    leads_count = graphene.NonNull(ConnectorSourceLeadCountType)

    class Meta:
        model = UnifiedConnector
        only_fields = (
            'id',
            'title',
            'is_active',
        )

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_unified_connector_qs(info)

    @staticmethod
    def resolve_leads_count(root, info, **_):
        return info.context.dl.unified_connector.unified_connector_leads_count.load(root.id)

    @staticmethod
    def resolve_sources(root, info, **_):
        return info.context.dl.unified_connector.unified_connector_sources.load(root.id)


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
    source_count_without_ingnored_and_added = graphene.Field(graphene.Int)

    @staticmethod
    def resolve_source_count_without_ingnored_and_added(root, info, **kwargs):
        qs = ConnectorSourceLead.objects.filter(
            source__unified_connector__project=info.context.active_project,
            source__unified_connector__is_active=True,
        ).exclude(
            Q(blocked=True) |
            Q(already_added=True)
        )
        if PP.check_permission(info, PP.Permission.VIEW_UNIFIED_CONNECTOR):
            return qs.count()
        return

    @staticmethod
    def resolve_unified_connectors(root, info, **kwargs) -> QuerySet:
        return get_unified_connector_qs(info)

    @staticmethod
    def resolve_connector_sources(root, info, **kwargs) -> QuerySet:
        return get_connector_source_qs(info)

    @staticmethod
    def resolve_connector_source_leads(root, info, **kwargs) -> QuerySet:
        qs = get_connector_source_lead_qs(info)
        return qs


class RssFieldType(graphene.ObjectType):
    key = graphene.String()
    label = graphene.String()


class AtomFeedFieldType(graphene.ObjectType):
    key = graphene.String()
    label = graphene.String()


class Query:
    rss_fields = graphene.Field(graphene.List(graphene.NonNull(RssFieldType)), url=graphene.String())
    atom_feed_fields = graphene.Field(graphene.List(graphene.NonNull(AtomFeedFieldType)), url=graphene.String())

    @staticmethod
    def resolve_rss_fields(root, info, url):
        return RssFeed().query_fields({"feed-url": url})

    @staticmethod
    def resolve_atom_feed_fields(root, info, url):
        return AtomFeed().query_fields({"feed-url": url})

def get_presigned_url(object_key, expiration=3600):
	import boto3
	from botocore.exceptions import NoCredentialsError, PartialCredentialsError
	from deep import settings
	s3_client = boto3.client('s3', region_name=settings.AWS_S3_REGION_NAME,
	                         aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
	                         aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, )
	try:
		return s3_client.generate_presigned_url(
			'get_object',
			Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': object_key},
			ExpiresIn=expiration
		)
	except (NoCredentialsError, PartialCredentialsError) as e:
		print(f"Error generating presigned URL: {e}")
		return None
