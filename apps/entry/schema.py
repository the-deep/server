import graphene

from django.db.models import QuerySet
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.common import has_prefetched
from utils.graphene.enums import EnumDescription
from utils.graphene.types import CustomDjangoListObjectType, ClientIdMixin
from utils.graphene.fields import DjangoPaginatedListObjectField, DjangoListField
from user_resource.schema import UserResourceMixin
from deep.permissions import ProjectPermissions as PP
from lead.models import Lead
from quality_assurance.schema import EntryReviewCommentType
from user.schema import UserType

from analysis_framework.models import Widget
from analysis_framework.enums import WidgetWidgetTypeEnum
from geo.schema import ProjectGeoAreaType

from .models import (
    Entry,
    Attribute,
)
from .enums import EntryTagTypeEnum
from .filter_set import EntryGQFilterSet


def get_entry_qs(info):
    entry_qs = Entry.objects.filter(
        # Filter by project
        project=info.context.active_project,
        # Filter by project's active analysis_framework (Only show active AF's entries)
        analysis_framework=info.context.active_project.analysis_framework_id,
    )
    # Generate queryset according to permission
    if PP.check_permission(info, PP.Permission.VIEW_ENTRY):
        if PP.check_permission(info, PP.Permission.VIEW_ALL_LEAD):
            return entry_qs
        elif PP.check_permission(info, PP.Permission.VIEW_ONLY_UNPROTECTED_LEAD):
            return entry_qs.filter(lead__confidentiality=Lead.Confidentiality.UNPROTECTED)
    return Entry.objects.none()


class EntryGroupLabelType(graphene.ObjectType):
    """
    NOTE: Data is generated from entry_project_labels [EntryProjectLabelsLoader]
    """
    label_id = graphene.ID(required=True)
    label_title = graphene.String(required=True)
    label_color = graphene.String()
    count = graphene.Int(required=True)
    groups = graphene.List(graphene.NonNull(graphene.String), required=True)


class AttributeType(ClientIdMixin, DjangoObjectType):
    # NOTE: This is only used by EntryType (Some attributes are pre-loaded using dataloader at parent type)
    class Meta:
        model = Attribute
        skip_registry = True
        fields = (
            'id', 'data', 'widget_version',
            'client_id',
        )

    widget = graphene.ID(required=True)
    widget_version = graphene.Int(required=True)
    widget_type = graphene.Field(WidgetWidgetTypeEnum, required=True)
    widget_type_display = EnumDescription(source='get_widget_type', required=True)
    # NOTE: This requires region_title and admin_level_title to be annotated
    geo_selected_options = graphene.List(graphene.NonNull(ProjectGeoAreaType))

    @staticmethod
    def resolve_widget(root, info, **_):
        return root.widget_id

    @staticmethod
    def resolve_widget_type(root, info, **_):
        return root.widget_type  # This is added from EntryType.resolve_attributes dataloader

    @staticmethod
    def resolve_geo_selected_options(root, info, **_):
        if root.widget_type == Widget.WidgetType.GEO and root.data and root.data.get('value'):
            return info.context.dl.entry.attribute_geo_selected_options.load(
                tuple(root.data['value'])  # needs to be hashable
            )


class EntryType(UserResourceMixin, ClientIdMixin, DjangoObjectType):
    class Meta:
        model = Entry
        fields = (
            'id',
            'lead', 'project', 'analysis_framework', 'information_date', 'order',
            'excerpt', 'dropped_excerpt', 'image', 'tabular_field', 'highlight_hidden',
            'controlled', 'controlled_changed_by',
            'client_id',
        )

    entry_type = graphene.Field(EntryTagTypeEnum, required=True)
    entry_type_display = EnumDescription(source='get_entry_type_display', required=True)
    attributes = graphene.List(graphene.NonNull(AttributeType))
    project_labels = graphene.List(graphene.NonNull(EntryGroupLabelType))
    verified_by = DjangoListField(UserType)
    verified_by_count = graphene.Int(required=True)
    review_comments = graphene.List(graphene.NonNull(EntryReviewCommentType))
    review_comments_count = graphene.Int(required=True)

    # project_labels TODO:
    # tabular_field TODO:

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_entry_qs(info)

    @staticmethod
    def resolve_project_labels(root, info, **kwargs):
        return info.context.dl.entry.entry_project_labels.load(root.pk)

    @staticmethod
    def resolve_attributes(root, info, **kwargs):
        return info.context.dl.entry.entry_attributes.load(root.pk)

    @staticmethod
    def resolve_review_comments(root, info, **kwargs):
        return info.context.dl.entry.review_comments.load(root.pk)

    @staticmethod
    def resolve_review_comments_count(root, info, **kwargs):
        return info.context.dl.entry.review_comments_count.load(root.pk)

    @staticmethod
    def resolve_verified_by(root, info, **kwargs):
        # Use cache if available
        if has_prefetched(root, 'verified_by'):
            return root.verified_by.all()
        return info.context.dl.entry.verified_by.load(root.pk)

    @staticmethod
    def resolve_verified_by_count(root, info, **kwargs):
        # Use cache if available
        if has_prefetched(root, 'verified_by'):
            return len(root.verified_by.all())
        return info.context.dl.entry.verified_by_count.load(root.pk)


class EntryListType(CustomDjangoListObjectType):
    class Meta:
        model = Entry
        filterset_class = EntryGQFilterSet


class Query:
    entry = DjangoObjectField(EntryType)
    entries = DjangoPaginatedListObjectField(
        EntryListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def resolve_entries(root, info, **kwargs) -> QuerySet:
        return get_entry_qs(info)
