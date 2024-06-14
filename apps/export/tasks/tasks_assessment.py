import copy

from ary.export import get_export_data_for_assessments
from assessment_registry.models import AssessmentRegistry
from export.assessments import NewExcelExporter
from export.exporters import JsonExporter
from export.models import Export
from lead.filter_set import LeadGQFilterSet
from lead.models import Lead

from deep.filter_set import get_dummy_request
from deep.permissions import ProjectPermissions as PP


def _export_assessments(export, AssessmentModel, excel_sheet_data_generator):
    user = export.exported_by
    project = export.project
    export_type = export.export_type
    is_preview = export.is_preview

    arys = AssessmentModel.objects.filter(project=project).select_related("project").distinct()
    if AssessmentModel == AssessmentRegistry:  # Filter is only available for Assessments (not PlannedAssessment)
        user_project_permissions = PP.get_permissions(project, user)
        filters = copy.deepcopy(export.filters)  # Avoid mutating database values
        # Lead filtered queryset
        leads_qs = Lead.objects.filter(project=export.project)
        if PP.Permission.VIEW_ALL_LEAD not in user_project_permissions:
            leads_qs = leads_qs.filter(confidentiality=Lead.Confidentiality.UNPROTECTED)
        dummy_request = get_dummy_request(active_project=project)
        leads_qs = LeadGQFilterSet(data=filters, queryset=leads_qs, request=dummy_request).qs
        arys = arys.filter(lead__in=leads_qs)
    iterable_arys = arys[: Export.PREVIEW_ASSESSMENT_SIZE] if is_preview else arys

    if export_type == Export.ExportType.JSON:
        exporter = JsonExporter()
        exporter.data = {ary.project.title: ary.to_exportable_json() for ary in iterable_arys}
        export_data = exporter.export()
    elif export_type == Export.ExportType.EXCEL:
        sheets_data = excel_sheet_data_generator(iterable_arys)
        export_data = NewExcelExporter(sheets_data).export()
    else:
        raise Exception(f"(Assessments Export) Unkown Export Type Provided: {export_type} for Export: {export.id}")

    return export_data


def export_assessments(export):
    return _export_assessments(export, AssessmentRegistry, get_export_data_for_assessments)
