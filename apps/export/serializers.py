import graphene

from django.db import transaction
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from graphene_django.filter.utils import get_filtering_args_from_filterset

from utils.graphene.fields import generate_serializer_field_class
from deep.serializers import (
    RemoveNullFieldsMixin,
    ProjectPropertySerializerMixin,
    StringIDField,
)
from lead.filter_set import LeadGQFilterSet
from analysis_framework.models import Widget, Exportable
from .tasks import export_task
from .models import Export


class ExportSerializer(RemoveNullFieldsMixin, DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Serializer for export
    """

    class Meta:
        model = Export
        exclude = ('filters',)


# ------------------- Graphql Serializers ----------------------------------------
# ---- [Start] ExportReportLevel Serialisers
class ExportReportLevelWidgetSubSubLevelSerializer(serializers.Serializer):  # Additional sub-level For matrix2d
    id = StringIDField(help_text='Matrix2D: {column-key}-{row-key}-{sub-row-key}')
    title = serializers.CharField(help_text='Matrix2D: {sub-row-label}')


class ExportReportLevelWidgetSubLevelSerializer(serializers.Serializer):
    id = StringIDField(help_text='Matrix1D: {row-key}-{cell-key}, Matrix2D: {column-key}-{row-key}')
    title = serializers.CharField(help_text='Matrix1D: {cell-label}, Matrix2D: {row-label}')
    sublevels = ExportReportLevelWidgetSubSubLevelSerializer(many=True, required=False, help_text='For 2D matrix')


class ExportReportLevelWidgetLevelSerializer(serializers.Serializer):
    id = StringIDField(help_text='Matrix1D: {row-key}, Matrix2D: {column-key}')
    title = serializers.CharField(help_text='Matrix1D: {row-label}, Matrix2D: {column-label}')
    sublevels = ExportReportLevelWidgetSubLevelSerializer(many=True, required=False, help_text='Not required for uncategorized data')


class ExportReportLevelWidgetSerializer(serializers.Serializer):
    # apps/analysis_framework/widgets/matrix2d_widget.py::'levels'
    # apps/analysis_framework/widgets/matrix1d_widget.py::'levels'
    """
    Matrix 1D
    {
        id: widget-id,
        'levels': [
            {
                'id': row-key,
                'title': row-label,
                'sublevels': [
                    {
                        'id': '{row-key}-{cell-key}',
                        'title': cell-label,
                    } for cell in row.get('cells', [])
                ],
            } for row in rows
        ],
    }

    Matrix 2D
    {
        id: widget-id,
        'levels': [
            {
                'id': column-key,
                'title': column-label',
                'sublevels': [
                    {
                        'id': '{column-key}-{row-key}',
                        'title': row-label,
                        'sublevels': [
                            {
                                'id': '{column-key}-{row-key}-{sub-row-key}',
                                'title': sub_row-label,
                            } for sub_row
                            in row.get('subRows', [])
                        ]
                    } for row in properties.get('rows', [])
                ],
            } for column in properties.get('columns', [])
        ],
    }
    """
    id = StringIDField(help_text='Widget ID')
    levels = ExportReportLevelWidgetLevelSerializer(many=True, required=False, help_text='Widget levels')


# ---- [End] ExportReportLevel Serialisers
# ---- [Start] ExportReportStructure Serialisers
class ExportReportStructureWidgetThirdLevelSerializer(serializers.Serializer):  # Additional sub-level For matrix2d
    id = StringIDField(help_text='Matrix2D: {column-key}-{row-key}-{sub-row-key}')


class ExportReportStructureWidgetSecondLevelSerializer(serializers.Serializer):
    id = StringIDField(help_text='Matrix1D: {row-key}-{cell-key}, Matrix2D: {column-key}-{row-key}')
    levels = ExportReportStructureWidgetThirdLevelSerializer(many=True, required=False, help_text='For 2D matrix')


class ExportReportStructureWidgetFirstLevelSerializer(serializers.Serializer):
    id = StringIDField(help_text='Matrix1D: {row-key}, Matrix2D: {column-key}')
    levels = ExportReportStructureWidgetSecondLevelSerializer(many=True, required=False, help_text='Not required for uncategorized data')


class ExportReportStructureWidgetSerializer(serializers.Serializer):
    """
    # NOTE: valid key can be moved up/down on the levels
    Matrix 1D
    {
        id: widget-id,
        'levels': [
            {
                'id': row-key,
                'levels': [
                    {
                        'id': '{row-key}-{cell-key}',
                    } for cell in row.get('cells', [])
                ],
            } for row in rows
        ],
    }

    Matrix 2D
    {
        id: widget-id,
        'levels': [
            {
                'id': column-key,
                'levels': [
                    {
                        'id': '{column-key}-{row-key}',
                        'levels': [
                            {
                                'id': '{column-key}-{row-key}-{sub-row-key}',
                            } for sub_row
                            in row.get('subRows', [])
                        ]
                    } for row in properties.get('rows', [])
                ],
            } for column in properties.get('columns', [])
        ],
    }
    """
    id = StringIDField(help_text='Widget ID')
    levels = ExportReportStructureWidgetFirstLevelSerializer(many=True, required=False, help_text='Widget levels')

# ---- [End] ExportReportStructure Serialisers


class ExportCreateGqlSerializer(ProjectPropertySerializerMixin, serializers.ModelSerializer):
    SUPPORTED_EXPORT_TYPES_BY_DATE_TYPE = {
        Export.DataType.ENTRIES: [
            Export.ExportType.EXCEL,
            Export.ExportType.REPORT,
            Export.ExportType.JSON,
        ],
        Export.DataType.ASSESSMENTS: [
            Export.ExportType.EXCEL,
        ],
        Export.DataType.PLANNED_ASSESSMENTS: [
            Export.ExportType.EXCEL,
        ],
    }

    SUPPORTED_FORMATS_BY_EXPORT_TYPE = {
        Export.ExportType.EXCEL: [
            Export.Format.XLSX,
        ],
        Export.ExportType.REPORT: [
            Export.Format.DOCX,
            Export.Format.PDF,
        ],
        Export.ExportType.JSON: [
            Export.Format.JSON,
        ],
    }

    class Meta:
        model = Export
        fields = (
            'title',  # Data type (entries, assessments, ..)
            'type',  # Data type (entries, assessments, ..)
            'format',  # xlsx, docx, pdf, ...
            'export_type',  # excel, report, json, ...
            'is_preview',
            'filters',
            # Specific arguments for exports additional configuration
            'excel_decoupled',
            'report_show_groups',
            'report_show_lead_entry_id',
            'report_show_assessment_data',
            'report_show_entry_widget_data',
            'report_text_widget_ids',
            'report_exporting_widgets',
            'report_levels',
            'report_structure',
        )

    # Excel
    excel_decoupled = serializers.BooleanField(
        help_text='Don\'t group entries tags. Slower export generation.', required=False)

    # Report
    report_show_groups = serializers.BooleanField(required=False)
    report_show_lead_entry_id = serializers.BooleanField(required=False)
    report_show_assessment_data = serializers.BooleanField(required=False)
    report_show_entry_widget_data = serializers.BooleanField(required=False)
    report_text_widget_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True, required=False)
    report_exporting_widgets = serializers.ListField(child=serializers.IntegerField(), allow_empty=True, required=False)
    report_levels = ExportReportLevelWidgetSerializer(
        required=False, many=True, help_text=ExportReportLevelWidgetSerializer.__doc__)
    report_structure = ExportReportStructureWidgetSerializer(
        required=False, many=True, help_text=ExportReportStructureWidgetSerializer.__doc__)

    filters = generate_serializer_field_class(
        type(
            'ExportLeadsEntriesFilterData',
            (graphene.InputObjectType,),
            get_filtering_args_from_filterset(LeadGQFilterSet, 'lead.schema.LeadListType')
        ),
        serializers.JSONField,
    )()

    @property
    def widget_qs(self):
        return Widget.objects.filter(analysis_framework=self.project.analysis_framework_id)

    @property
    def exportable_qs(self):
        return Exportable.objects.filter(analysis_framework=self.project.analysis_framework_id)

    def validate_filters(self, filters):
        filter_set = LeadGQFilterSet(data=filters)
        if not filter_set.is_valid():
            raise serializers.ValidationError(filter_set.errors)
        return filters

    def validate_report_text_widget_ids(self, widget_ids):
        if widget_ids:
            text_widgets_id = self.widget_qs.filter(widget_id=Widget.WidgetType.TEXT).values_list('id', flat=True)
            return [
                widget_id
                for widget_id in widget_ids
                if widget_id in text_widgets_id
            ]
        return []

    def validate_report_exporting_widgets(self, widget_ids):
        if widget_ids:
            widgets_id = self.widget_qs.values_list('id', flat=True)
            return [
                widget_id
                for widget_id in widget_ids
                if widget_id in widgets_id
            ]
        return []

    # TODO: def validate_report_levels(self, widget_ids):
    # TODO: def validate_report_structure(self, widget_ids):

    def validate(self, data):
        # NOTE: We only need to check with create logic (as update is not allowed)
        # Validate type, export_type and format
        data_type = data['type']
        export_type = data['export_type']
        _format = data['format']
        if export_type not in self.SUPPORTED_EXPORT_TYPES_BY_DATE_TYPE[data_type]:
            raise serializers.ValidationError(f'Unsupported Export type: {export_type} for Data type: {data_type}')
        if _format not in self.SUPPORTED_FORMATS_BY_EXPORT_TYPE[export_type]:
            raise serializers.ValidationError(f'Unsupported Format: {_format} for Export Type: {export_type}')
        return data

    def update(self, _):
        raise serializers.ValidationError('Update isn\'t allowed for Export')

    def create(self, data):
        data['exported_by'] = self.context['request'].user
        data['project'] = self.project
        data['extra_options'] = {
            key: data.pop(key)
            for key in (
                'excel_decoupled',
                # Report
                'report_show_groups',
                'report_show_lead_entry_id',
                'report_show_assessment_data',
                'report_show_entry_widget_data',
                'report_text_widget_ids',
                'report_exporting_widgets',
                'report_levels',
                'report_structure',
            ) if key in data
        }
        export = super().create(data)
        transaction.on_commit(
            lambda: export.set_task_id(export_task.delay(export.id).id)
        )
        return export
