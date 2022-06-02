import graphene

from django.db.models import QuerySet
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from deep.serializers import URLCachedFileField
from utils.graphene.types import CustomDjangoListObjectType, FileFieldType
from utils.graphene.fields import DjangoPaginatedListObjectField, generate_type_for_serializer

from lead.schema import (
    LeadsFilterDataType,
    LeadFilterDataType,
    get_lead_filter_data,
)

from .serializers import (
    ExportReportLevelWidgetSerializer,
    ExportReportStructureWidgetSerializer,
)
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


UserExportReportLevelWidgetType = generate_type_for_serializer(
    'UserExportReportLevelWidgetType',
    serializer_class=ExportReportLevelWidgetSerializer,
)

UserExportReportStructureWidgetType = generate_type_for_serializer(
    'UserExportReportStructureWidgetType',
    serializer_class=ExportReportStructureWidgetSerializer,
)


class UserExportTypeExtraOptions(graphene.ObjectType):
    # -- Excel
    excel_decoupled = graphene.Boolean(description='Don\'t group entries tags. Slower export generation.')
    # -- Report
    report_show_groups = graphene.Boolean()
    report_show_lead_entry_id = graphene.Boolean()
    report_show_assessment_data = graphene.Boolean()
    report_show_entry_widget_data = graphene.Boolean()
    report_text_widget_ids = graphene.List(graphene.NonNull(graphene.Int))
    report_exporting_widgets = graphene.List(graphene.NonNull(graphene.Int))
    report_levels = graphene.List(
        graphene.NonNull(UserExportReportLevelWidgetType),
        description=ExportReportLevelWidgetSerializer.__doc__,
    )
    report_structure = graphene.List(
        graphene.NonNull(UserExportReportStructureWidgetType),
        description=ExportReportStructureWidgetSerializer.__doc__,
    )


class UserExportType(DjangoObjectType):
    class Meta:
        model = Export
        only_fields = (
            'id', 'project', 'is_preview', 'title',
            'mime_type', 'extra_options', 'exported_by',
            'exported_at', 'started_at', 'ended_at', 'pending', 'is_archived',
            'analysis',
        )

    project = graphene.ID(source='project_id')
    format = graphene.Field(graphene.NonNull(ExportFormatEnum))
    type = graphene.Field(graphene.NonNull(ExportDataTypeEnum))
    status = graphene.Field(graphene.NonNull(ExportStatusEnum))
    export_type = graphene.Field(graphene.NonNull(ExportExportTypeEnum))
    file = graphene.Field(FileFieldType)
    file_download_url = graphene.String()
    # Filter Data
    filters = graphene.Field(LeadsFilterDataType)
    filters_data = graphene.Field(LeadFilterDataType)
    extra_options = graphene.NonNull(UserExportTypeExtraOptions)

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_export_qs(info)

    @staticmethod
    def resolve_filters_data(root, info):
        return get_lead_filter_data(root.filters, info.context)

    @staticmethod
    def resolve_file_download_url(root, info, **kwargs):
        return info.context.request.build_absolute_uri(
            URLCachedFileField.generate_url(
                root.file.name,
                parameters={
                    'ResponseContentDisposition': f'filename = "{root.title}.{root.format}"'
                }
            )
        )


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
