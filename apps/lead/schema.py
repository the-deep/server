import graphene
from typing import Union
from django.db.models import QuerySet
from graphene_django import DjangoObjectType, DjangoListField
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from deep.permissions import ProjectPermissions as PP
from organization.schema import OrganizationType

from .models import Lead, LeadPreview
from .filter_set import LeadGQFilterSet


def get_lead_qs(info):
    lead_qs = Lead.objects.filter(project=info.context.active_project)
    # Generate querset according to permission
    if PP.check_permission(info, PP.Permission.VIEW_ALL_LEAD):
        return lead_qs
    elif PP.check_permission(info, PP.Permission.VIEW_ONLY_UNPROTECTED_LEAD):
        return lead_qs.filter(confidentiality=Lead.UNPROTECTED)
    return Lead.objects.none()


class LeadPreviewType(DjangoObjectType):
    class Meta:
        model = LeadPreview
        fields = (
            'text_extract',
            'thumbnail',
            'thumbnail_height',
            'thumbnail_width',
            'word_count',
            'page_count',
            # 'classified_doc_id',
            # 'classification_status',
        )


class VerifiedStatType(graphene.ObjectType):
    total_count = graphene.Int()
    verified_count = graphene.Int()


class LeadType(DjangoObjectType):
    class Meta:
        model = Lead
        fields = (
            'id', 'title', 'created_by', 'created_at', 'modified_by', 'modified_at',
            'project', 'lead_group', 'assignee', 'published_on',
            'source_type', 'priority', 'confidentiality', 'status',
            'text', 'url', 'website', 'attachment', 'emm_entities'
        )

    project = graphene.ID(source='project_id')
    lead_preview = graphene.Field(LeadPreviewType)
    source = graphene.Field(OrganizationType)
    authors = DjangoListField(OrganizationType)
    verified_stat = graphene.Field(VerifiedStatType)

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_lead_qs(info)

    @staticmethod
    def resolve_lead_preview(root, info, **kwargs) -> Union[int, None]:
        return info.context.dl.lead.lead_preview.load(root.pk)

    @staticmethod
    def resolve_verified_stat(root, info, **kwargs):
        # TODO: Use entry filter here as well
        return info.context.dl.lead.verified_stat.load(root.pk)


class LeadListType(CustomDjangoListObjectType):
    class Meta:
        model = Lead
        filterset_class = LeadGQFilterSet


class Query:
    lead = DjangoObjectField(LeadType)
    leads = DjangoPaginatedListObjectField(
        LeadListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def resolve_leads(root, info, **kwargs) -> QuerySet:
        return get_lead_qs(info)
