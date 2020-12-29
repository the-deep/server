from ary.models import Assessment, PlannedAssessment
from ary.export import (
    get_export_data_for_assessments,
    get_export_data_for_planned_assessments,
)
from export.models import Export
from export.exporters import JsonExporter
from export.assessments import ExcelExporter, NewExcelExporter


def export_assessments(export):
    project = export.project
    export_type = export.export_type
    is_preview = export.is_preview

    arys = Assessment.objects.filter(lead__project=project).distinct()
    if export_type == Export.JSON:
        exporter = JsonExporter()
        exporter.data = {
            ary.lead.project.title: ary.to_exportable_json()
            for ary in arys
        }
        export_data = exporter.export(export, export.type.title())
    elif export_type == Export.EXCEL:
        sheets_data = get_export_data_for_assessments(arys)
        export_data = NewExcelExporter(sheets_data)\
            .export(is_preview)
    else:
        raise Exception(
            '(Assessments Export) Unkown Export Type Provided: {} for Export:'.format(export_type, export.id),
        )

    return export_data


def export_planned_assessments(export):
    project = export.project
    export_type = export.export_type
    is_preview = export.is_preview

    arys = PlannedAssessment.objects.filter(project=project).distinct()
    if export_type == Export.JSON:
        exporter = JsonExporter()
        exporter.data = {
            ary.project.title: ary.to_exportable_json()
            for ary in arys
        }
        export_data = exporter.export(export, export.type.title())
    elif export_type == Export.EXCEL:
        sheets_data = get_export_data_for_planned_assessments(arys)
        export_data = NewExcelExporter(sheets_data)\
            .export(is_preview)
    else:
        raise Exception(
            '(Assessments Export) Unkown Export Type Provided: {} for Export:'.format(export_type, export.id),
        )

    return export_data
