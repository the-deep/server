import copy

from deep.permissions import ProjectPermissions as PP
from analysis_framework.models import Exportable
from entry.models import Entry
from export.models import Export
from export.entries.excel_exporter import ExcelExporter
from export.entries.report_exporter import ReportExporter
from export.entries.json_exporter import JsonExporter
from geo.models import Region
from lead.models import Lead
from lead.filter_set import LeadGQFilterSet
from entry.filter_set import EntryGQFilterSet


def export_entries(export):
    user = export.exported_by
    project = export.project
    export_type = export.export_type
    is_preview = export.is_preview

    user_project_permissions = PP.get_permissions(project, user)

    # Avoid mutating database values
    filters = copy.deepcopy(export.filters)
    extra_options = copy.deepcopy(export.extra_options)

    # Lead/Entry filtered queryset
    leads_qs = Lead.objects.filter(project=export.project)
    if PP.Permission.VIEW_ALL_LEAD not in user_project_permissions:
        leads_qs = leads_qs.filter(confidentiality=Lead.Confidentiality.UNPROTECTED)
    # Lead and Entry FilterSet needs request to work with active_project
    dummy_request = LeadGQFilterSet.get_dummy_request(project)
    leads_qs = LeadGQFilterSet(data=filters, queryset=leads_qs, request=dummy_request).qs
    entries_qs = EntryGQFilterSet(
        data=filters.get('entries_filter_data'),
        request=dummy_request,
        queryset=Entry.objects.filter(
            project=export.project,
            analysis_framework=export.project.analysis_framework_id,
            lead__in=leads_qs,
        )
    ).qs

    # Prefetches
    entries_qs = entries_qs.prefetch_related('entrygrouplabel_set')
    entries_qs = Entry.get_exportable_queryset(entries_qs).prefetch_related(
        'lead__authors',
        'lead__authors__organization_type',
        # Also organization parents
        'lead__authors__parent',
        'lead__authors__parent__organization_type',
    )

    exportables = Exportable.objects.filter(
        analysis_framework__project=project,
        exportdata__isnull=False,
    ).distinct()
    regions = Region.objects.filter(project=project).distinct()

    if export_type == Export.ExportType.EXCEL:
        decoupled = extra_options.get('excel_decoupled', False)
        export_data = ExcelExporter(entries_qs, decoupled, project.id, is_preview=is_preview)\
            .load_exportables(exportables, regions)\
            .add_entries(entries_qs)\
            .export()

    elif export_type == Export.ExportType.REPORT:
        # which widget data needs to be exported along with
        exporting_widgets = extra_options.get('report_exporting_widgets', [])
        report_show_attributes = dict(
            show_lead_entry_id=extra_options.get('report_show_lead_entry_id', True),
            show_assessment_data=extra_options.get('report_show_assessment_data', True),
            show_entry_widget_data=extra_options.get('report_show_entry_widget_data', True),
        )

        report_structure = extra_options.get('report_structure')
        report_levels = extra_options.get('report_levels')
        text_widget_ids = extra_options.get('report_text_widget_ids') or []
        show_groups = extra_options.get('report_show_groups')
        export_data = (
            ReportExporter(
                exporting_widgets=exporting_widgets,
                is_preview=is_preview,
                **report_show_attributes,
            ).load_exportables(exportables, regions)
            .load_levels(report_levels)
            .load_structure(report_structure)
            .load_group_lables(entries_qs, show_groups)
            .load_text_from_text_widgets(entries_qs, text_widget_ids)
            .add_entries(entries_qs)
            .export(pdf=export.format == Export.Format.PDF)
        )

    elif export_type == Export.ExportType.JSON:
        export_data = JsonExporter(is_preview=is_preview)\
            .load_exportables(exportables)\
            .add_entries(entries_qs)\
            .export()

    else:
        raise Exception(
            '(Entries Export) Unkown Export Type Provided: {export_type} for Export: {export.id}'
        )

    return export_data
