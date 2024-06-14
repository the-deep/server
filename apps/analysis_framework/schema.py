from typing import Union

import graphene
from assisted_tagging.models import PredictionTagAnalysisFrameworkWidgetMapping
from django.db.models import QuerySet
from graphene.types.generic import GenericScalar
from graphene_django import DjangoListField, DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination
from project.models import ProjectMembership
from project.schema import AnalysisFrameworkVisibleProjectType

from deep.permissions import AnalysisFrameworkPermissions as AfP
from utils.graphene.enums import EnumDescription
from utils.graphene.fields import (
    DjangoPaginatedListObjectField,
    generate_type_for_serializer,
)
from utils.graphene.types import (
    ClientIdMixin,
    CustomDjangoListObjectType,
    FileFieldType,
)

from .enums import (
    AnalysisFrameworkRoleTypeEnum,
    WidgetFilterTypeEnum,
    WidgetWidgetTypeEnum,
    WidgetWidthTypeEnum,
)
from .filter_set import AnalysisFrameworkGqFilterSet, AnalysisFrameworkTagGqFilterSet
from .models import (
    AnalysisFramework,
    AnalysisFrameworkMembership,
    AnalysisFrameworkRole,
    AnalysisFrameworkTag,
    Exportable,
    Filter,
    Section,
    Widget,
)
from .public_schema import PublicAnalysisFrameworkListType
from .serializers import AnalysisFrameworkPropertiesGqlSerializer

AnalysisFrameworkPropertiesType = generate_type_for_serializer(
    "AnalysisFrameworkPropertiesType",
    serializer_class=AnalysisFrameworkPropertiesGqlSerializer,
)


class WidgetConditionalType(graphene.ObjectType):
    parent_widget = graphene.ID(required=True)
    parent_widget_type = graphene.Field(WidgetWidgetTypeEnum, required=True)
    conditions = GenericScalar()


class WidgetType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = Widget
        only_fields = (
            "id",
            "title",
            "order",
            "properties",
            "version",
        )

    widget_id = graphene.Field(WidgetWidgetTypeEnum, required=True)
    widget_id_display = EnumDescription(source="get_widget_id_display", required=True)
    width = graphene.Field(WidgetWidthTypeEnum, required=True)
    width_display = EnumDescription(source="get_width_display", required=True)
    key = graphene.String(required=True)
    version = graphene.Int(required=True)
    conditional = graphene.Field(WidgetConditionalType)

    @staticmethod
    def resolve_conditional(root, info, **_):
        if root.conditional_parent_widget_id:
            return dict(
                parent_widget=root.conditional_parent_widget_id,
                parent_widget_type=root.conditional_parent_widget_type,
                conditions=root.conditional_conditions,
            )


class SectionType(ClientIdMixin, DjangoObjectType):
    widgets = DjangoListField(WidgetType)

    class Meta:
        model = Section
        only_fields = (
            "id",
            "title",
            "order",
            "tooltip",
        )

    @staticmethod
    def resolve_widgets(root, info):
        return info.context.dl.analysis_framework.sections_widgets.load(root.id)


class AnalysisFrameworkTagType(DjangoObjectType):
    class Meta:
        model = AnalysisFrameworkTag
        only_fields = (
            "id",
            "title",
            "description",
        )

    icon = graphene.Field(FileFieldType, required=False)


class AnalysisFrameworkProjectCount(graphene.ObjectType):
    project_count = graphene.Int(required=True)
    test_project_count = graphene.Int(required=True)


# NOTE: We have AnalysisFrameworkDetailType for detailed AF Type.
class AnalysisFrameworkType(DjangoObjectType):
    class Meta:
        model = AnalysisFramework
        only_fields = (
            "id",
            "title",
            "description",
            "is_private",
            "assisted_tagging_enabled",
            "organization",
            "created_by",
            "created_at",
            "modified_by",
            "modified_at",
        )

    current_user_role = graphene.Field(AnalysisFrameworkRoleTypeEnum)
    preview_image = graphene.Field(FileFieldType)
    export = graphene.Field(FileFieldType)
    cloned_from = graphene.ID(source="cloned_from_id")
    allowed_permissions = graphene.List(
        graphene.NonNull(
            graphene.Enum.from_enum(AfP.Permission),
        ),
        required=True,
    )
    tags = graphene.List(
        graphene.NonNull(
            AnalysisFrameworkTagType,
        ),
        required=True,
    )
    used_in_project_count = graphene.Field(AnalysisFrameworkProjectCount, required=True)

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

    @staticmethod
    def resolve_tags(root, info):
        return info.context.dl.analysis_framework.af_tags.load(root.id)

    @staticmethod
    def resolve_used_in_project_count(root, info):
        return info.context.dl.analysis_framework.af_project_count.load(root.id)


class AnalysisFrameworkRoleType(DjangoObjectType):
    class Meta:
        model = AnalysisFrameworkRole
        only_fields = (
            "id",
            "title",
            "is_private_role",
            "is_default_role",
        )

    type = graphene.Field(AnalysisFrameworkRoleTypeEnum)


class AnalysisFrameworkFilterType(DjangoObjectType):
    class Meta:
        model = Filter
        only_fields = (
            "id",
            "title",
            "properties",
            "widget_key",
        )

    key = graphene.String(required=True)
    widget_type = graphene.Field(WidgetWidgetTypeEnum, required=True)
    widget_type_display = EnumDescription(source="get_widget_type_display", required=True)
    filter_type = graphene.Field(WidgetFilterTypeEnum, required=True)
    filter_type_display = EnumDescription(source="get_filter_type_display", required=True)

    @staticmethod
    def resolve_widget_type(root, info, **kwargs):
        return root.widget_type  # NOTE: This is added from AnalysisFrameworkDetailType.resolve_filters dataloader


class AnalysisFrameworkExportableType(DjangoObjectType):
    class Meta:
        model = Exportable
        only_fields = (
            "id",
            "inline",
            "order",
            "data",
        )

    widget_key = graphene.String(required=True)
    widget_type = graphene.Field(WidgetWidgetTypeEnum, required=True)
    widget_type_display = EnumDescription(source="get_widget_type_display", required=True)

    @staticmethod
    def resolve_widget_type(root, info, **kwargs):
        return root.widget_type  # NOTE: This is added from AnalysisFrameworkDetailType.resolve_exportables dataloader


class AnalysisFrameworkMembershipType(ClientIdMixin, DjangoObjectType):
    class Meta:
        model = AnalysisFrameworkMembership
        only_fields = ("id", "member", "role", "joined_at", "added_by")


class AnalysisFrameworkPredictionMappingType(ClientIdMixin, DjangoObjectType):
    widget = graphene.ID(source="widget_id", required=True)
    widget_type = graphene.Field(WidgetWidgetTypeEnum, required=True)
    tag = graphene.ID(source="tag_id")

    class Meta:
        model = PredictionTagAnalysisFrameworkWidgetMapping
        only_fields = (
            "id",
            "widget",
            "tag",
            "association",
        )

    @staticmethod
    def resolve_widget_type(root, info, **kwargs):
        return root.widget.widget_id  # TODO: Dataloaders


class AnalysisFrameworkDetailType(AnalysisFrameworkType):
    primary_tagging = DjangoListField(SectionType)  # With section
    secondary_tagging = DjangoListField(WidgetType)  # Without section
    members = DjangoListField(AnalysisFrameworkMembershipType)
    filters = DjangoListField(AnalysisFrameworkFilterType)
    exportables = DjangoListField(AnalysisFrameworkExportableType)
    preview_image = graphene.Field(FileFieldType)
    export = graphene.Field(FileFieldType)
    visible_projects = DjangoListField(AnalysisFrameworkVisibleProjectType)
    prediction_tags_mapping = graphene.List(
        graphene.NonNull(
            AnalysisFrameworkPredictionMappingType,
        ),
    )
    properties = graphene.Field(AnalysisFrameworkPropertiesType)

    class Meta:
        model = AnalysisFramework
        skip_registry = True
        only_fields = (
            "id",
            "title",
            "description",
            "is_private",
            "assisted_tagging_enabled",
            "organization",
            "created_by",
            "created_at",
            "modified_by",
            "modified_at",
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
    def resolve_prediction_tags_mapping(root, info):
        project_membership_qs = ProjectMembership.objects.filter(
            project__analysis_framework=root,
            member=info.context.request.user,
        )
        if root.get_current_user_role(info.context.request.user) is not None or project_membership_qs.exists():
            return PredictionTagAnalysisFrameworkWidgetMapping.objects.filter(
                widget__analysis_framework=root,
            ).all()  # TODO: Dataloaders
        return []


class AnalysisFrameworkListType(CustomDjangoListObjectType):
    class Meta:
        model = AnalysisFramework
        filterset_class = AnalysisFrameworkGqFilterSet


class AnalysisFrameworkTagListType(CustomDjangoListObjectType):
    class Meta:
        model = AnalysisFrameworkTag
        filterset_class = AnalysisFrameworkTagGqFilterSet


class Query:
    analysis_framework = DjangoObjectField(AnalysisFrameworkDetailType)
    analysis_frameworks = DjangoPaginatedListObjectField(
        AnalysisFrameworkListType, pagination=PageGraphqlPagination(page_size_query_param="pageSize")
    )
    public_analysis_frameworks = DjangoPaginatedListObjectField(
        PublicAnalysisFrameworkListType, pagination=PageGraphqlPagination(page_size_query_param="pageSize")
    )
    analysis_framework_tags = DjangoPaginatedListObjectField(
        AnalysisFrameworkTagListType, pagination=PageGraphqlPagination(page_size_query_param="pageSize")
    )
    analysis_framework_roles = graphene.List(graphene.NonNull(AnalysisFrameworkRoleType), required=True)

    @staticmethod
    def resolve_analysis_frameworks(root, info, **kwargs) -> QuerySet:
        return AnalysisFramework.get_for_gq(info.context.user).distinct()

    @staticmethod
    def resolve_public_analysis_frameworks(root, info, **kwargs) -> QuerySet:
        return AnalysisFramework.objects.filter(is_private=False).distinct()

    @staticmethod
    def resolve_analysis_framework_roles(root, info, **kwargs) -> QuerySet:
        return AnalysisFrameworkRole.objects.all()
