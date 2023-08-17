import graphene
from functools import reduce
from typing import Union
from django.db import models
from django.db.models import QuerySet
from graphene_django import DjangoObjectType, DjangoListField
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.pagination import NoOrderingPageGraphqlPagination
from utils.graphene.enums import EnumDescription
from utils.graphene.types import CustomDjangoListObjectType, ClientIdMixin
from utils.graphene.fields import DjangoPaginatedListObjectField

from user.models import User
from organization.models import Organization, OrganizationType as OrganizationTypeModel
from geo.models import GeoArea
from analysis_framework.models import Filter as AfFilter, Widget

from user_resource.schema import UserResourceMixin
from deep.permissions import ProjectPermissions as PP
from deep.permalinks import Permalink
from organization.schema import OrganizationType, OrganizationTypeType
from user.schema import UserType
from geo.schema import ProjectGeoAreaType

from lead.filter_set import LeadsFilterDataType


from .models import (
    Lead,
    LeadGroup,
    LeadPreview,
    LeadEMMTrigger,
    EMMEntity,
    UserSavedLeadFilter,
)
from .enums import (
    LeadConfidentialityEnum,
    LeadStatusEnum,
    LeadPriorityEnum,
    LeadSourceTypeEnum,
    LeadExtractionStatusEnum,
)
from .filter_set import (
    LeadGQFilterSet,
    LeadGroupGQFilterSet,
)


def get_lead_qs(info):
    lead_qs = Lead.objects.filter(project=info.context.active_project)
    # Generate queryset according to permission
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


# Generates database level objects used in filters.
def get_lead_filter_data(filters, context):
    def _filter_by_id(entity_list, entity_id_list):
        return [
            entity
            for entity in entity_list
            if entity.id in entity_id_list
        ]

    def _id_to_int(ids):
        return [
            int(_id) for _id in ids
        ]

    if filters is None or not isinstance(filters, dict):
        return {}

    entry_filter_data = filters.get('entries_filter_data') or {}
    geo_widget_filter_keys = AfFilter.objects.filter(
        analysis_framework=context.active_project.analysis_framework_id,
        widget_key__in=Widget.objects.filter(
            analysis_framework=context.active_project.analysis_framework_id,
            widget_id=Widget.WidgetType.GEO,
        ).values_list('key', flat=True)
    ).values_list('key', flat=True)

    # Lead Filter Data
    created_by_ids = _id_to_int(filters.get('created_by') or [])
    modified_by_ids = _id_to_int(filters.get('modified_by') or [])
    assignee_ids = _id_to_int(filters.get('assignees') or [])
    author_organization_type_ids = _id_to_int(filters.get('authoring_organization_types') or [])
    author_organization_ids = _id_to_int(filters.get('author_organizations') or [])
    source_organization_ids = _id_to_int(filters.get('source_organizations') or [])
    # Entry Filter Data
    ef_lead_assignee_ids = _id_to_int(entry_filter_data.get('lead_assignees') or [])
    ef_lead_authoring_organizationtype_ids = _id_to_int(entry_filter_data.get('lead_authoring_organization_types') or [])
    ef_lead_author_organization_ids = _id_to_int(entry_filter_data.get('lead_author_organizations') or [])
    ef_lead_source_organization_ids = _id_to_int(entry_filter_data.get('lead_source_organizations') or [])
    ef_lead_created_by_ids = _id_to_int(entry_filter_data.get('lead_created_by') or [])
    ef_created_by_ids = _id_to_int(entry_filter_data.get('created_by') or [])
    ef_modified_by_ids = _id_to_int(entry_filter_data.get('modified_by') or [])
    ef_geo_area_ids = set(
        _id_to_int(
            reduce(
                lambda a, b: a + b,
                [
                    filterable_data['value_list'] or []
                    for filterable_data in entry_filter_data.get('filterable_data') or []
                    if filterable_data.get('filter_key') in geo_widget_filter_keys and filterable_data.get('value_list')
                ], []
            )
        )
    )

    # Prefetch all data
    users = list(
        User.objects.filter(
            projectmembership__project=context.active_project,
            id__in=set([
                *created_by_ids,
                *modified_by_ids,
                *assignee_ids,
                *ef_created_by_ids,
                *ef_lead_assignee_ids,
                *ef_lead_created_by_ids,
                *ef_modified_by_ids,
            ])
        ).order_by('id')
    )

    organizations = list(
        Organization.objects.filter(
            id__in=set([
                *author_organization_ids,
                *source_organization_ids,
                *ef_lead_author_organization_ids,
                *ef_lead_source_organization_ids,
            ])
        ).order_by('id')
    )

    organization_types = list(
        OrganizationTypeModel.objects.filter(
            id__in=set([
                *author_organization_type_ids,
                *ef_lead_authoring_organizationtype_ids,
            ])
        ).order_by('id')
    )

    geoareas = list(
        GeoArea.objects.filter(
            admin_level__region__project=context.active_project,
            id__in=ef_geo_area_ids
        ).order_by('id')
    )

    return dict(
        created_by_options=_filter_by_id(users, created_by_ids),
        modified_by_options=_filter_by_id(users, modified_by_ids),
        assignee_options=_filter_by_id(users, assignee_ids),
        author_organization_type_options=_filter_by_id(organization_types, author_organization_type_ids),
        author_organization_options=_filter_by_id(organizations, author_organization_ids),
        source_organization_options=_filter_by_id(organizations, source_organization_ids),
        entry_filter_lead_assignee_options=_filter_by_id(users, ef_lead_assignee_ids),
        entry_filter_lead_authoring_organization_type_options=_filter_by_id(
            organization_types, ef_lead_authoring_organizationtype_ids
        ),
        entry_filter_lead_author_organization_options=_filter_by_id(organizations, ef_lead_author_organization_ids),
        entry_filter_lead_source_organization_options=_filter_by_id(organizations, ef_lead_source_organization_ids),
        entry_filter_lead_created_by_options=_filter_by_id(users, ef_lead_created_by_ids),
        entry_filter_created_by_options=_filter_by_id(users, ef_created_by_ids),
        entry_filter_modified_by_options=_filter_by_id(users, ef_modified_by_ids),
        entry_filter_geo_area_options=_filter_by_id(geoareas, ef_geo_area_ids),
    )


class LeadPreviewType(DjangoObjectType):
    class Meta:
        model = LeadPreview
        only_fields = (
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
        only_fields = ('id', 'emm_keyword', 'emm_risk_factor', 'count')

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
        only_fields = ('id', 'name')

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


class LeadFilterDataType(graphene.ObjectType):
    created_by_options = graphene.List(graphene.NonNull(UserType), required=True)
    modified_by_options = graphene.List(graphene.NonNull(UserType), required=True)
    assignee_options = graphene.List(graphene.NonNull(UserType), required=True)
    author_organization_type_options = graphene.List(graphene.NonNull(OrganizationTypeType), required=True)
    author_organization_options = graphene.List(graphene.NonNull(OrganizationType), required=True)
    source_organization_options = graphene.List(graphene.NonNull(OrganizationType), required=True)

    entry_filter_created_by_options = graphene.List(graphene.NonNull(UserType), required=True)
    entry_filter_lead_assignee_options = graphene.List(graphene.NonNull(UserType), required=True)
    entry_filter_lead_author_organization_options = graphene.List(graphene.NonNull(OrganizationType), required=True)
    entry_filter_lead_authoring_organization_type_options = graphene.List(
        graphene.NonNull(OrganizationTypeType), required=True,
    )
    entry_filter_lead_created_by_options = graphene.List(graphene.NonNull(UserType), required=True)
    entry_filter_lead_source_organization_options = graphene.List(graphene.NonNull(OrganizationType), required=True)
    entry_filter_modified_by_options = graphene.List(graphene.NonNull(UserType), required=True)
    entry_filter_geo_area_options = graphene.List(graphene.NonNull(ProjectGeoAreaType), required=True)


class UserSavedLeadFilterType(DjangoObjectType):
    filters = graphene.Field(LeadsFilterDataType)
    filters_data = graphene.Field(LeadFilterDataType)

    class Meta:
        model = UserSavedLeadFilter
        only_fields = (
            'id',
            'title',
            'created_at',
            'modified_at',
        )

    @staticmethod
    def resolve_filters_data(root, info):
        return get_lead_filter_data(root.filters, info.context)


class LeadGroupType(UserResourceMixin, DjangoObjectType):
    class Meta:
        model = LeadGroup
        only_fields = (
            'id',
            'title',
            'project',
        )
    lead_counts = graphene.Int(required=True)

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_lead_group_qs(info)

    @staticmethod
    def resolve_lead_counts(root, info, **kwargs):
        return info.context.dl.lead.leadgroup_lead_counts.load(root.pk)


class LeadGroupListType(CustomDjangoListObjectType):
    class Meta:
        model = LeadGroup
        filterset_class = LeadGroupGQFilterSet


# LeadDetailType is defined for detailed (nested) attributes.
class LeadType(UserResourceMixin, ClientIdMixin, DjangoObjectType):
    class Meta:
        model = Lead
        only_fields = (
            'id', 'title', 'is_assessment_lead', 'lead_group', 'assignee', 'published_on',
            'text', 'url', 'attachment',
            'client_id',
        )

    project = graphene.ID(source='project_id', required=True)
    # Enums
    source_type = graphene.Field(LeadSourceTypeEnum, required=True)
    source_type_display = EnumDescription(source='get_source_type_display', required=True)
    priority = graphene.Field(LeadPriorityEnum, required=True)
    priority_display = EnumDescription(source='get_priority_display', required=True)
    confidentiality = graphene.Field(LeadConfidentialityEnum, required=True)
    confidentiality_display = EnumDescription(source='get_confidentiality_display', required=True)
    status = graphene.Field(LeadStatusEnum, required=True)
    status_display = EnumDescription(source='get_status_display', required=True)

    extraction_status = graphene.Field(LeadExtractionStatusEnum)
    lead_preview = graphene.Field(LeadPreviewType)
    source = graphene.Field(OrganizationType)
    authors = DjangoListField(OrganizationType)
    assignee = graphene.Field(UserType)
    lead_group = graphene.Field(LeadGroupType)
    # EMM Fields
    emm_entities = DjangoListField(EmmEntityType)
    emm_triggers = DjangoListField(LeadEmmTriggerType)
    assessment_id = graphene.ID()
    # Entries count
    entries_count = graphene.Field(EntriesCountType)
    filtered_entries_count = graphene.Int(
        description=(
            'Count used to order or filter-out leads'
            '. Can be =null or =entries_count->total or !=entries_count->total.'
        )
    )
    # Duplicate leads
    duplicate_leads_count = graphene.Int()

    # For external accessible link
    share_view_url = graphene.String(required=True)

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_lead_qs(info)

    @staticmethod
    def resolve_assignee(root, info, **kwargs) -> Union[User, None]:
        return root.get_assignee()

    @staticmethod
    def resolve_assessment_id(root, info, **kwargs) -> Union[User, None]:
        return info.context.dl.lead.assessment_id.load(root.pk)

    @staticmethod
    def resolve_source(root, info, **kwargs) -> Union[User, None]:
        return root.source_id and info.context.dl.lead.source_organization.load(root.source_id)

    @staticmethod
    def resolve_authors(root, info, **kwargs) -> Union[User, None]:
        return info.context.dl.lead.author_organizations.load(root.pk)

    @staticmethod
    def resolve_lead_preview(root, info, **kwargs) -> Union[int, None]:
        return info.context.dl.lead.lead_preview.load(root.pk)

    @staticmethod
    def resolve_entries_count(root, info, **kwargs):
        return info.context.dl.lead.entries_count.load(root.pk)

    @staticmethod
    def resolve_filtered_entries_count(root, info, **kwargs):
        # filtered_entry_count is from LeadFilterSet
        return getattr(root, 'filtered_entry_count', None)

    @staticmethod
    def resolve_share_view_url(root: Lead, info, **kwargs):
        return Permalink.lead_share_view(root.uuid)

    def resolve_attachment(root, info, **kwargs):
        return info.context.dl.deep_gallery.file.load(root.attachment_id)


class LeadDetailType(LeadType):
    class Meta:
        model = Lead
        skip_registry = True
        only_fields = (
            'id', 'title', 'is_assessment_lead', 'lead_group', 'assignee', 'published_on',
            'text', 'url', 'attachment',
            'client_id',
        )

    entries = graphene.List(graphene.NonNull('entry.schema.EntryType'))

    @staticmethod
    def resolve_entries(root, info, **kwargs):
        return root.entry_set.filter(
            analysis_framework=info.context.active_project.analysis_framework,
        ).all()

    def resolve_attachment(root, info, **kwargs):
        return info.context.dl.deep_gallery.file.load(root.attachment_id)


class LeadListType(CustomDjangoListObjectType):
    class Meta:
        model = Lead
        filterset_class = LeadGQFilterSet


class Query:
    lead = DjangoObjectField(LeadDetailType)
    leads = DjangoPaginatedListObjectField(
        LeadListType,
        pagination=NoOrderingPageGraphqlPagination(
            page_size_query_param='pageSize',
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

    user_saved_lead_filter = graphene.Field(UserSavedLeadFilterType)

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

    @staticmethod
    def resolve_user_saved_lead_filter(root, info, **kwargs):
        if root.get_current_user_role(info.context.request.user) is not None:
            return UserSavedLeadFilter.objects.filter(
                user=info.context.user,
                project=info.context.active_project,
            ).first()
