from django.db import transaction

from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from utils.graphene.fields import generate_serializer_field_class
from deep.serializers import (
    RemoveNullFieldsMixin,
    ProjectPropertySerializerMixin,
    StringIDField,
    GraphqlSupportDrfSerializerJSONField,
)
from lead.filter_set import LeadGQFilterSet, LeadsFilterDataInputType
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
class ExportReportLevelWidgetFourthLevelSerializer(serializers.Serializer):
    """
     Additional sub-level (sub-column) For matrix2d
    """
    id = StringIDField(help_text='Matrix2D: {column-key}-{sub-column}-{row-key}-{sub-row-key}')
    title = serializers.CharField(help_text='Matrix2D: {sub-column-label}')


class ExportReportLevelWidgetSubSubLevelSerializer(serializers.Serializer):  # Additional sub-level For matrix2d
    id = StringIDField(help_text='Matrix2D: {column-key}-{row-key}-{sub-row-key}')
    title = serializers.CharField(help_text='Matrix2D: {sub-row-label}')
    sublevels = ExportReportLevelWidgetFourthLevelSerializer(
        many=True,
        required=False,
        help_text='For 2D matrix (sub-column)',
    )


class ExportReportLevelWidgetSubLevelSerializer(serializers.Serializer):
    id = StringIDField(help_text='Matrix1D: {row-key}-{cell-key}, Matrix2D: {column-key}-{row-key}')
    title = serializers.CharField(help_text='Matrix1D: {cell-label}, Matrix2D: {row-label}')
    sublevels = ExportReportLevelWidgetSubSubLevelSerializer(many=True, required=False, help_text='For 2D matrix')


class ExportReportLevelWidgetLevelSerializer(serializers.Serializer):
    id = StringIDField(help_text='Matrix1D: {row-key}, Matrix2D: {column-key}')
    title = serializers.CharField(help_text='Matrix1D: {row-label}, Matrix2D: {column-label}')
    sublevels = ExportReportLevelWidgetSubLevelSerializer(
        many=True, required=False, help_text='Not required for uncategorized data')


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
                                'sublevels': [
                                    {
                                        'id': '{column_key}-{sub_column}-{row_key}-{sub_row_key}',
                                        'title': sub_column-label,
                                    } for sub_row
                                    in row.get('subColumns', [])
                                ]
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
class ExportReportStructureWidgetFourthLevelSerializer(serializers.Serializer):
    """
     Additional sub-level (sub-column) For matrix2d
    """
    id = StringIDField(help_text='Matrix2D: {column-key}-{sub-column}-{row-key}-{sub-row-key}')


class ExportReportStructureWidgetThirdLevelSerializer(serializers.Serializer):
    """
    # Additional sub-level (sub-row) For matrix2d
    """
    id = StringIDField(help_text='Matrix2D: {column-key}-{row-key}-{sub-row-key}')
    levels = ExportReportStructureWidgetFourthLevelSerializer(
        many=True,
        required=False,
        help_text='For 2D matrix (sub-column)',
    )


class ExportReportStructureWidgetSecondLevelSerializer(serializers.Serializer):
    id = StringIDField(help_text='Matrix1D: {row-key}-{cell-key}, Matrix2D: {column-key}-{row-key}')
    levels = ExportReportStructureWidgetThirdLevelSerializer(many=True, required=False, help_text='For 2D matrix')


class ExportReportStructureWidgetFirstLevelSerializer(serializers.Serializer):
    id = StringIDField(help_text='Matrix1D: {row-key}, Matrix2D: {column-key}')
    levels = ExportReportStructureWidgetSecondLevelSerializer(
        many=True, required=False, help_text='Not required for uncategorized data')


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
        id: '{widget_id}',
        'levels': [
            {
                'id': '{column_key}',
                'levels': [
                    {
                        'id': '{column_key}-{row_key}',
                        'levels': [
                            {
                                'id': '{column_key}-{row_key}-{sub_row_key}',
                                'levels': [
                                    {
                                        'id': '{column_key}-{sub_column}-{row_key}-{sub_row_key}',
                                    } for sub_column in row.get('subColumns', [])
                                ],
                            } for sub_row in row.get('subRows', [])
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


class ExportExcelSelectedColumnSerializer(serializers.Serializer):
    is_widget = serializers.BooleanField(required=True)
    widget_key = serializers.CharField(required=False)
    static_column = serializers.ChoiceField(choices=Export.StaticColumn.choices, required=False)

    def validate(self, data):
        if data['is_widget']:
            if data.get('widget_key') is None:
                raise serializers.ValidationError('widget_key key is required when is widget is True')
        elif data.get('static_column') is None:
            raise serializers.ValidationError('static_column is required when is widget is False')
        return data


class ExportExtraOptionsSerializer(ProjectPropertySerializerMixin, serializers.Serializer):
    # Excel
    excel_decoupled = serializers.BooleanField(
        help_text="Don't group entries tags. Slower export generation.", required=False)
    excel_columns = ExportExcelSelectedColumnSerializer(
        required=False,
        many=True,
        help_text=ExportExcelSelectedColumnSerializer.__doc__,
    )

    # Report
    report_show_groups = serializers.BooleanField(required=False)
    report_show_lead_entry_id = serializers.BooleanField(required=False)
    report_show_assessment_data = serializers.BooleanField(required=False)
    report_show_entry_widget_data = serializers.BooleanField(required=False)
    report_text_widget_ids = serializers.ListField(child=StringIDField(), allow_empty=True, required=False)
    report_exporting_widgets = serializers.ListField(child=StringIDField(), allow_empty=True, required=False)
    report_levels = ExportReportLevelWidgetSerializer(
        required=False, many=True, help_text=ExportReportLevelWidgetSerializer.__doc__)
    report_structure = ExportReportStructureWidgetSerializer(
        required=False, many=True, help_text=ExportReportStructureWidgetSerializer.__doc__)


class UserExportBaseGqlMixin(ProjectPropertySerializerMixin, serializers.ModelSerializer):
    title = serializers.CharField(required=False)

    class Meta:
        model = Export
        fields = (
            'title',
            'type',  # Data type (entries, assessments, ..)
            'format',  # xlsx, docx, pdf, ...
            'export_type',  # excel, report, json, ...
            'is_preview',
            'filters',
            'extra_options',
            'analysis',
        )

    filters = generate_serializer_field_class(LeadsFilterDataInputType, GraphqlSupportDrfSerializerJSONField)()
    extra_options = ExportExtraOptionsSerializer(required=False)

    @property
    def widget_qs(self):
        return Widget.objects.filter(analysis_framework=self.project.analysis_framework_id)

    @property
    def exportable_qs(self):
        return Exportable.objects.filter(analysis_framework=self.project.analysis_framework_id)

    def validate_title(self, title):
        existing_exports = Export.objects.filter(
            title=title,
            project=self.project,
            exported_by=self.context['request'].user,
        )
        if self.instance:
            existing_exports = existing_exports.exclude(id=self.instance.id)
        if existing_exports.exists():
            raise serializers.ValidationError(f'Title {title} already exists.')
        return title

    def validate_filters(self, filters):
        filter_set = LeadGQFilterSet(data=filters, request=self.context['request'])
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

    def validate_analysis(self, analysis):
        if analysis and analysis.project != self.project:
            raise serializers.ValidationError(
                f"Analysis project {analysis.project_id} doesn't match current project {self.project.id}"
            )
        return analysis


class UserExportCreateGqlSerializer(UserExportBaseGqlMixin, serializers.ModelSerializer):
    def validate(self, data):
        # NOTE: We only need to check with create logic (as update only have title for now)
        # Validate type, export_type and format
        data_type = data['type']
        export_type = data['export_type']
        _format = data['format']
        if (data_type, export_type, _format) not in Export.DEFAULT_TITLE_LABEL:
            raise serializers.ValidationError(f'Unsupported Export request: {(data_type, export_type, _format)}')
        return data

    def create(self, data):
        data['title'] = data.get('title') or Export.generate_title(data['type'], data['export_type'], data['format'])
        data['exported_by'] = self.context['request'].user
        data['project'] = self.project
        export = super().create(data)
        transaction.on_commit(
            lambda: export.set_task_id(export_task.delay(export.id).id)
        )
        return export

    def update(self, _):
        raise serializers.ValidationError('Not allowed using this serializer.')


class UserExportUpdateGqlSerializer(UserExportBaseGqlMixin, serializers.ModelSerializer):
    class Meta:
        model = Export
        fields = (
            'title',
        )

    def create(self, _):
        raise serializers.ValidationError('Not allowed using this serializer.')
