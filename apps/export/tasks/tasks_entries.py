import copy

from django.db import models

from deep.permissions import ProjectPermissions as PP
from deep.filter_set import get_dummy_request
from analysis_framework.models import Exportable, Widget
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
    dummy_request = get_dummy_request(active_project=project)
    leads_qs = LeadGQFilterSet(data=filters, queryset=leads_qs, request=dummy_request).qs.prefetch_related(
        'authors',
        'authors__organization_type',
        # Also organization parents
        'authors__parent',
        'authors__parent__organization_type',
    )
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
    entries_qs = entries_qs.prefetch_related(
        'entrygrouplabel_set',
        models.Prefetch(
            'lead',
            queryset=Lead.objects.annotate(
                page_count=models.F('leadpreview__page_count'),
            ).prefetch_related(
                'authors',
                'authors__organization_type',
                # Also organization parents
                'authors__parent',
                'authors__parent__organization_type',
            ),
        ),
    )
    widget = Widget.objects.filter(
        analysis_framework__project=project,
        is_deleted=False
    ).values('key')

    exportables = Exportable.objects.filter(
        analysis_framework__project=project,
        widget_key__in=widget
    ).distinct()
    regions = Region.objects.filter(project=project).distinct()

    date_format = extra_options.get('date_format')

    if export_type == Export.ExportType.EXCEL:
        decoupled = extra_options.get('excel_decoupled', False)
        columns = extra_options.get('excel_columns')
        export_data = ExcelExporter(
            export,
            entries_qs,
            project,
            date_format,
            columns=columns,
            decoupled=decoupled,
            is_preview=is_preview,
        )\
            .load_exportables(exportables, regions)\
            .add_entries(entries_qs)\
            .export(leads_qs)

    elif export_type == Export.ExportType.REPORT:
        # which widget data needs to be exported along with
        exporting_widgets = extra_options.get('report_exporting_widgets', [])
        report_show_attributes = dict(
            show_lead_entry_id=extra_options.get('report_show_lead_entry_id', True),
            show_assessment_data=extra_options.get('report_show_assessment_data', True),
            show_entry_widget_data=extra_options.get('report_show_entry_widget_data', True),
        )

        citation_style = extra_options.get('report_citation_style')
        report_structure = extra_options.get('report_structure')
        report_levels = extra_options.get('report_levels')
        text_widget_ids = extra_options.get('report_text_widget_ids') or []
        show_groups = extra_options.get('report_show_groups')
        export_data = (
            ReportExporter(
                date_format,
                citation_style,
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
            .load_exportables(exportables, project.analysis_framework)\
            .add_entries(entries_qs)\
            .export()

    else:
        raise Exception(
            '(Entries Export) Unkown Export Type Provided: {export_type} for Export: {export.id}'
        )

    return export_data
