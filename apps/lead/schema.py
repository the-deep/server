import graphene
from typing import Union
from django.db import models
from django.db.models import QuerySet
from graphene_django import DjangoObjectType, DjangoListField
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.enums import EnumDescription
from utils.graphene.types import CustomDjangoListObjectType, ClientIdMixin
from utils.graphene.fields import DjangoPaginatedListObjectField
from deep.permissions import ProjectPermissions as PP
from organization.schema import OrganizationType
from user.models import User
from user_resource.schema import UserResourceMixin

from user.schema import UserType

from .models import (
    Lead,
    LeadGroup,
    LeadPreview,
    LeadEMMTrigger,
    EMMEntity,
)
from .enums import (
    LeadConfidentialityEnum,
    LeadStatusEnum,
    LeadPriorityEnum,
    LeadSourceTypeEnum,
)
from .filter_set import (
    LeadGQFilterSet,
    LeadGroupGQFilterSet
)


def get_lead_qs(info):
    lead_qs = Lead.objects.filter(project=info.context.active_project)
    # Generate querset according to permission
    if PP.check_permission(info, PP.Permission.VIEW_ALL_LEAD):
        return lead_qs
    elif PP.check_permission(info, PP.Permission.VIEW_ONLY_UNPROTECTED_LEAD):
        return lead_qs.filter(confidentiality=Lead.Confidentiality.UNPROTECTED)
    return Lead.objects.none()


def get_lead_group_qs(info):
    lead_group_qs = LeadGroup.objects.filter(project=info.context.active_project)
    if PP.check_permission(info, PP.Permission.VIEW_ALL_LEAD):
        return lead_group_qs
    return LeadGroup.objects.none()


def get_emm_entities_qs(info):
    emm_entity_qs = EMMEntity.objects.filter(lead__project=info.context.active_project).distinct()
    if PP.check_permission(info, PP.Permission.VIEW_ALL_LEAD):
        return emm_entity_qs
    elif PP.check_permission(info, PP.Permission.VIEW_ONLY_UNPROTECTED_LEAD):
        return emm_entity_qs.filter(lead__confidentiality=Lead.Confidentiality.UNPROTECTED)
    return EMMEntity.objects.none()


def get_lead_emm_entities_qs(info):
    lead_emm_qs = LeadEMMTrigger.objects.filter(lead__project=info.context.active_project)
    if PP.check_permission(info, PP.Permission.VIEW_ALL_LEAD):
        return lead_emm_qs
    elif PP.check_permission(info, PP.Permission.VIEW_ONLY_UNPROTECTED_LEAD):
        return lead_emm_qs.filter(lead__confidentiality=Lead.Confidentiality.UNPROTECTED)
    return LeadEMMTrigger.objects.none()


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


class LeadEmmTriggerType(DjangoObjectType):
    class Meta:
        model = LeadEMMTrigger
        fields = ('id', 'emm_keyword', 'emm_risk_factor', 'count')

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_lead_emm_entities_qs(info)


class LeadEmmTriggerListType(CustomDjangoListObjectType):
    class Meta:
        model = LeadEMMTrigger
        filterset_class = []


class EmmEntityType(DjangoObjectType):
    class Meta:
        model = EMMEntity
        fields = ('id', 'name')

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_emm_entities_qs(info)


class EmmEntityListType(CustomDjangoListObjectType):
    class Meta:
        model = EMMEntity
        filterset_class = []


class EmmKeyWordType(graphene.ObjectType):
    emm_keywords = graphene.String()


class EmmKeyRiskFactorType(graphene.ObjectType):
    emm_risk_factors = graphene.String()


class EntriesCountType(graphene.ObjectType):
    total = graphene.Int()
    controlled = graphene.Int()


class LeadGroupType(UserResourceMixin, DjangoObjectType):
    class Meta:
        model = LeadGroup
        fields = (
            'id',
            'title',
            'project',
        )
    lead_counts = graphene.Field(graphene.Int)

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_lead_group_qs(info)

    @staticmethod
    def resolve_lead_counts(root, info, **kwargs):
        return info.context.dl.lead.lead_counts.load(root.pk)


class LeadGroupListType(CustomDjangoListObjectType):
    class Meta:
        model = LeadGroup
        filterset_class = LeadGroupGQFilterSet


# LeadDetailType is defined for detailed (nested) attributes.
class LeadType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = Lead
        fields = (
            'id', 'title', 'created_by', 'created_at', 'modified_by', 'modified_at',
            'is_assessment_lead', 'project', 'lead_group', 'assignee', 'published_on',
            'text', 'url', 'website', 'attachment',
            'client_id',
        )

    # Enums
    source_type = graphene.Field(LeadSourceTypeEnum, required=True)
    source_type_display = EnumDescription(source='get_source_type_display', required=True)
    priority = graphene.Field(LeadPriorityEnum, required=True)
    priority_display = EnumDescription(source='get_priority_display', required=True)
    confidentiality = graphene.Field(LeadConfidentialityEnum, required=True)
    confidentiality_display = EnumDescription(source='get_confidentiality_display', required=True)
    status = graphene.Field(LeadStatusEnum, required=True)
    status_display = EnumDescription(source='get_status_display', required=True)

    lead_preview = graphene.Field(LeadPreviewType)
    source = graphene.Field(OrganizationType)
    authors = DjangoListField(OrganizationType)
    entries_counts = graphene.Field(EntriesCountType)
    assignee = graphene.Field(UserType)
    lead_group = graphene.Field(LeadGroupType)
    # EMM Fields
    emm_entities = DjangoListField(EmmEntityType)
    emm_triggers = DjangoListField(LeadEmmTriggerType)

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_lead_qs(info)

    @staticmethod
    def resolve_assignee(root, info, **kwargs) -> Union[User, None]:
        return root.get_assignee()

    @staticmethod
    def resolve_lead_preview(root, info, **kwargs) -> Union[int, None]:
        return info.context.dl.lead.lead_preview.load(root.pk)

    @staticmethod
    def resolve_entries_counts(root, info, **kwargs):
        # TODO: Use entry filter here as well
        return info.context.dl.lead.entries_counts.load(root.pk)


class LeadDetailType(LeadType):
    class Meta:
        model = Lead
        skip_registry = True
        fields = (
            'id', 'title', 'created_by', 'created_at', 'modified_by', 'modified_at',
            'is_assessment_lead', 'project', 'lead_group', 'assignee', 'published_on',
            'text', 'url', 'website', 'attachment',
            'client_id',
        )

    entries = graphene.List(graphene.NonNull('entry.schema.EntryType'))

    @staticmethod
    def resolve_entries(root, info, **kwargs):
        return root.entry_set.filter(
            analysis_framework=info.context.active_project.analysis_framework,
        ).all()


class LeadListType(CustomDjangoListObjectType):
    class Meta:
        model = Lead
        filterset_class = LeadGQFilterSet


class Query:
    lead = DjangoObjectField(LeadDetailType)
    leads = DjangoPaginatedListObjectField(
        LeadListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
    lead_group = DjangoObjectField(LeadGroupType)
    lead_groups = DjangoPaginatedListObjectField(
        LeadGroupListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
    emm_entities = DjangoPaginatedListObjectField(
        EmmEntityListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
    lead_emm_triggers = DjangoPaginatedListObjectField(
        LeadEmmTriggerListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
    # TODO: Add Pagination
    emm_keywords = graphene.List(graphene.NonNull(EmmKeyWordType))
    emm_risk_factors = graphene.List(graphene.NonNull(EmmKeyRiskFactorType))

    @staticmethod
    def resolve_leads(root, info, **kwargs) -> QuerySet:
        return get_lead_qs(info)

    @staticmethod
    def resolve_lead_groups(root, info, **kwargs) -> QuerySet:
        return get_lead_group_qs(info)

    @staticmethod
    def resolve_emm_entities(root, info, **kwargs) -> QuerySet:
        return get_emm_entities_qs(info)

    @staticmethod
    def resolve_lead_emm_triggers(root, info, **kwargs) -> QuerySet:
        return get_lead_emm_entities_qs(info)

    @staticmethod
    def resolve_emm_keywords(root, info, **kwargs):
        return LeadEMMTrigger.objects.filter(
            lead__project=info.context.active_project
        ).values('emm_keyword').annotate(
            total_count=models.Sum('count'),
            key=models.F('emm_keyword'),
            label=models.F('emm_keyword')
        ).order_by('emm_keyword')

    @staticmethod
    def resolve_emm_risk_factors(root, info, **kwargs):
        return LeadEMMTrigger.objects.filter(
            ~models.Q(emm_risk_factor=''),
            ~models.Q(emm_risk_factor=None),
            lead__project=info.context.active_project,
        ).values('emm_risk_factor').annotate(
            total_count=models.Sum('count'),
            key=models.F('emm_risk_factor'),
            label=models.F('emm_risk_factor'),
        ).order_by('emm_risk_factor')
