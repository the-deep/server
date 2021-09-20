import graphene

from django.db.models import QuerySet
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType, ClientIdMixin
from utils.graphene.fields import DjangoPaginatedListObjectField
from deep.permissions import ProjectPermissions as PP
from lead.models import Lead
from quality_assurance.schema import EntryReviewCommentType

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
        analysis_framework=info.context.active_project.analysis_framework,
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
            'id', 'data',
            'client_id',
        )

    widget = graphene.ID(required=True)
    widget_type = graphene.Field(WidgetWidgetTypeEnum, required=True)
    # NOTE: This requires region_title and admin_level_title to be annotated
    # NOTE: Some item can be null (if missing from database)
    geo_selected_options = graphene.List(ProjectGeoAreaType)

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
                # TODO: Need to migrate out dict (custom polygon) from 'value'.
                tuple([
                    v
                    for v in root.data['value']
                    if type(v) in [str, int]
                ])  # needs to be hashable
            )


class EntryType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = Entry
        fields = (
            'id',
            'lead', 'project', 'analysis_framework', 'information_date', 'order',
            'excerpt', 'dropped_excerpt', 'image', 'tabular_field', 'highlight_hidden',
            'controlled', 'controlled_changed_by', 'verified_by',
            'client_id',
        )

    entry_type = graphene.Field(graphene.NonNull(EntryTagTypeEnum))
    attributes = graphene.List(graphene.NonNull(AttributeType))
    project_labels = graphene.List(graphene.NonNull(EntryGroupLabelType))
    review_comments = graphene.List(graphene.NonNull(EntryReviewCommentType))

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
