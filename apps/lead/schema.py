import graphene
from django.db.models import QuerySet
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from deep.permissions import ProjectPermissions as PP

from .models import Lead
from .filter_set import LeadGQFilterSet


def get_lead_qs(info):
    lead_qs = Lead.objects.filter(project=info.context.active_project)
    # Generate querset according to permission
    if PP.check_permission(info, PP.Permission.VIEW_ALL_LEAD):
        return lead_qs
    elif PP.check_permission(info, PP.Permission.VIEW_ONLY_UNPROTECTED_LEAD):
        return lead_qs.filter(confidentiality=Lead.UNPROTECTED)
    return Lead.objects.none()


class LeadType(DjangoObjectType):
    class Meta:
        model = Lead
        fields = (
            'id', 'project', 'lead_group',
            'title', 'assignee', 'published_on',
            'authors', 'source',
            'source_type', 'priority', 'confidentiality', 'status',
            'text', 'url', 'website', 'attachment', 'emm_entities'
        )

    project = graphene.ID(source='project_id')

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_lead_qs(info)


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
