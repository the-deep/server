import graphene
import json
from djangorestframework_camel_case.render import CamelCaseJSONRenderer

from django.db.models import QuerySet
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType, FileFieldType
from utils.graphene.fields import DjangoPaginatedListObjectField

from .models import Export
from .filter_set import ExportGQLFilterSet
from .enums import (
    ExportDataTypeEnum,
    ExportFormatEnum,
    ExportStatusEnum,
    ExportExportTypeEnum
)


def get_export_qs(info):
    return Export.objects.filter(
        project=info.context.active_project,
        exported_by=info.context.request.user,
        is_deleted=False,
    )


class UserExportType(DjangoObjectType):
    class Meta:
        model = Export
        only_fields = (
            'id', 'project', 'is_preview', 'title',
            'filters', 'mime_type', 'extra_options', 'exported_by',
            'exported_at', 'started_at', 'ended_at', 'pending', 'is_archived',
            'analysis',
        )

    project = graphene.ID(source='project_id')
    format = graphene.Field(graphene.NonNull(ExportFormatEnum))
    type = graphene.Field(graphene.NonNull(ExportDataTypeEnum))
    status = graphene.Field(graphene.NonNull(ExportStatusEnum))
    export_type = graphene.Field(graphene.NonNull(ExportExportTypeEnum))
    file = graphene.Field(FileFieldType)

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_export_qs(info)

    @staticmethod
    def resolve_filters(root, info, **kwargs):
        # XXX: Better way?
        return json.loads(CamelCaseJSONRenderer().render(root.filters))


class UserExportListType(CustomDjangoListObjectType):
    class Meta:
        model = Export
        filterset_class = ExportGQLFilterSet


class Query:
    export = DjangoObjectField(UserExportType)
    exports = DjangoPaginatedListObjectField(
        UserExportListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def resolve_exports(root, info, **kwargs) -> QuerySet:
        return get_export_qs(info).filter(is_preview=False)
