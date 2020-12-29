from ary.models import Assessment, PlannedAssessment
from ary.export import (
    get_export_data_for_assessments,
    get_export_data_for_planned_assessments,
)
from export.models import Export
from export.exporters import JsonExporter
from export.assessments import NewExcelExporter


def _export_assessments(export, AssessmentModel, excel_sheet_data_generator):
    project = export.project
    export_type = export.export_type
    is_preview = export.is_preview

    arys = AssessmentModel.objects.filter(project=project).prefetch_related('project').distinct()
    iterable_arys = arys[:Export.PREVIEW_ASSESSMENT_SIZE] if is_preview else arys
    if export_type == Export.JSON:
        exporter = JsonExporter()
        exporter.data = {
            ary.project.title: ary.to_exportable_json()
            for ary in iterable_arys
        }
        export_data = exporter.export(export, export.type.title())
    elif export_type == Export.EXCEL:
        sheets_data = excel_sheet_data_generator(iterable_arys)
        export_data = NewExcelExporter(sheets_data)\
            .export()
    else:
        raise Exception(
            f'(Assessments Export) Unkown Export Type Provided: {export_type} for Export: {export.id}'
        )

    return export_data


def export_assessments(export):
    return _export_assessments(export, Assessment, get_export_data_for_assessments)


def export_planned_assessments(export):
    return _export_assessments(export, PlannedAssessment, get_export_data_for_planned_assessments)
