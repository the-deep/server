from typing import Union

import graphene
from graphene_django import DjangoObjectType, DjangoListField
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination
from django.db.models import QuerySet

from utils.graphene.enums import EnumDescription
from utils.graphene.types import CustomDjangoListObjectType, ClientIdMixin, FileFieldType
from utils.graphene.fields import DjangoPaginatedListObjectField
from deep.permissions import AnalysisFrameworkPermissions as AfP
from project.schema import AnalysisFrameworkVisibleProjectType

from .models import (
    AnalysisFramework,
    Section,
    Widget,
    Filter,
    Exportable,
    AnalysisFrameworkMembership,
    AnalysisFrameworkRole,
)
from .enums import (
    WidgetWidgetTypeEnum,
    WidgetWidthTypeEnum,
    WidgetFilterTypeEnum,
)
from .filter_set import AnalysisFrameworkGqFilterSet


class WidgetType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = Widget
        fields = (
            'id', 'title', 'order', 'properties',
            'client_id',
        )

    widget_id = graphene.Field(WidgetWidgetTypeEnum, required=True)
    widget_id_display = EnumDescription(source='get_widget_id_display', required=True)
    width = graphene.Field(WidgetWidthTypeEnum, required=True)
    width_display = EnumDescription(source='get_width_display', required=True)
    key = graphene.String(required=True)


class SectionType(ClientIdMixin, DjangoObjectType):
    widgets = DjangoListField(WidgetType)

    class Meta:
        model = Section
        fields = (
            'id', 'title', 'order', 'tooltip',
            'client_id',
        )

    @staticmethod
    def resolve_widgets(root, info):
        return info.context.dl.analysis_framework.sections_widgets.load(root.id)


# NOTE: We have AnalysisFrameworkDetailType for detailed AF Type.
class AnalysisFrameworkType(DjangoObjectType):
    class Meta:
        model = AnalysisFramework
        only_fields = (
            'id', 'title', 'description', 'is_private', 'organization',
            'created_by', 'created_at', 'modified_by', 'modified_at',
        )

    current_user_role = graphene.String()
    preview_image = graphene.Field(FileFieldType)
    allowed_permissions = graphene.List(
        graphene.NonNull(
            graphene.Enum.from_enum(AfP.Permission),
        ), required=True
    )

    @staticmethod
    def get_custom_node(_, info, id):
        try:
            af = AnalysisFramework.get_for_gq(info.context.user).get(pk=id)
            info.context.set_active_af(af)
            return af
        except AnalysisFramework.DoesNotExist:
            return None

    @staticmethod
    def resolve_current_user_role(root, info, **_) -> Union[str, None]:
        return root.get_current_user_role(info.context.request.user)

    @staticmethod
    def resolve_allowed_permissions(root, info):
        return AfP.get_permissions(
            root.get_current_user_role(info.context.request.user),
            is_public=not root.is_private,
        )


class AnalysisFrameworkRoleType(DjangoObjectType):
    class Meta:
        model = AnalysisFrameworkRole
        only_fields = ('id', 'title',)


class AnalysisFrameworkFilterType(DjangoObjectType):
    class Meta:
        model = Filter
        only_fields = ('id', 'title', 'properties',)

    key = graphene.String(required=True)
    widget_type = graphene.Field(WidgetWidgetTypeEnum, required=True)
    widget_type_display = EnumDescription(source='get_widget_type_display', required=True)
    filter_type = graphene.Field(WidgetFilterTypeEnum, required=True)
    filter_type_display = EnumDescription(source='get_filter_type_display', required=True)

    @staticmethod
    def resolve_widget_type(root, info, **kwargs):
        return root.widget_type  # NOTE: This is added from AnalysisFrameworkDetailType.resolve_filters dataloader


class AnalysisFrameworkExportableType(DjangoObjectType):
    class Meta:
        model = Exportable
        only_fields = ('id', 'inline', 'order', 'data',)

    widget_key = graphene.String(required=True)
    widget_type = graphene.Field(WidgetWidgetTypeEnum, required=True)
    widget_type_display = EnumDescription(source='get_widget_type_display', required=True)

    @staticmethod
    def resolve_widget_type(root, info, **kwargs):
        return root.widget_type  # NOTE: This is added from AnalysisFrameworkDetailType.resolve_exportables dataloader


class AnalysisFrameworkMembershipType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = AnalysisFrameworkMembership
        only_fields = ('id', 'member', 'role', 'joined_at', 'added_by')


class AnalysisFrameworkDetailType(AnalysisFrameworkType):
    primary_tagging = DjangoListField(SectionType)  # With section
    secondary_tagging = DjangoListField(WidgetType)  # Without section
    members = DjangoListField(AnalysisFrameworkMembershipType)
    filters = DjangoListField(AnalysisFrameworkFilterType)
    exportables = DjangoListField(AnalysisFrameworkExportableType)
    preview_image = graphene.Field(FileFieldType)
    visible_projects = DjangoListField(AnalysisFrameworkVisibleProjectType)

    class Meta:
        model = AnalysisFramework
        skip_registry = True
        only_fields = (
            'id', 'title', 'description', 'is_private', 'organization',
            'created_by', 'created_at', 'modified_by', 'modified_at',
            'properties',
        )

    @staticmethod
    def resolve_primary_tagging(root, info):
        return info.context.dl.analysis_framework.sections.load(root.id)

    @staticmethod
    def resolve_secondary_tagging(root, info):
        return info.context.dl.analysis_framework.secondary_widgets.load(root.id)

    @staticmethod
    def resolve_filters(root, info):
        return info.context.dl.analysis_framework.filters.load(root.id)

    @staticmethod
    def resolve_exportables(root, info):
        return info.context.dl.analysis_framework.exportables.load(root.id)

    @staticmethod
    def resolve_members(root, info):
        if root.get_current_user_role(info.context.request.user) is not None:
            return info.context.dl.analysis_framework.members.load(root.id)
        return []  # NOTE: Always return empty array FIXME: without empty everything is returned

    @staticmethod
    def resolve_visible_projects(root, info):
        return info.context.dl.analysis_framework.visible_projects.load(root.id)


class AnalysisFrameworkListType(CustomDjangoListObjectType):
    class Meta:
        model = AnalysisFramework
        filterset_class = AnalysisFrameworkGqFilterSet


class Query:
    analysis_framework = DjangoObjectField(AnalysisFrameworkDetailType)
    analysis_frameworks = DjangoPaginatedListObjectField(
        AnalysisFrameworkListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def resolve_analysis_frameworks(root, info, **kwargs) -> QuerySet:
        return AnalysisFramework.get_for_gq(info.context.user).distinct()
