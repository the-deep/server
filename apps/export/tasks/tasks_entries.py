import copy
from django.db import models

from analysis_framework.models import Exportable
from entry.filter_set import get_filtered_entries
from entry.models import Entry
from export.models import Export
from export.entries.excel_exporter import ExcelExporter
from export.entries.report_exporter import ReportExporter
from export.entries.json_exporter import JsonExporter
from geo.models import Region
from lead.models import Lead
from lead.filter_set import LeadFilterSet


def export_entries(export):
    user = export.exported_by
    project_id = export.project.id
    export_type = export.export_type
    is_preview = export.is_preview

    filters = copy.deepcopy(export.filters)
    # remove lead so that it can be used to include or exclude
    lead_ids = filters.pop('lead', [])
    include_leads = filters.pop('include_leads', True)

    # prepare entries filter data
    entries_filter_data = {
        f[0]: f[1] for f in filters.pop('entries_filter', [])
    }
    # project is necessary
    entries_filter_data['project'] = project_id
    # get filtered entries
    queryset = get_filtered_entries(user, entries_filter_data)

    filters['entries_filter_data'] = entries_filter_data
    if not include_leads:
        all_leads = Lead.get_for(
            user,
            filters
        )
        all_leads = LeadFilterSet(data=filters, queryset=all_leads).qs
        queryset = queryset.filter(
            lead_id__in=all_leads
        ).exclude(
            lead_id__in=lead_ids
        )
    else:
        queryset = queryset.filter(
            lead_id__in=lead_ids
        )
    queryset = queryset.prefetch_related(
        'entrygrouplabel_set'
    )
    queryset = Entry.get_exportable_queryset(queryset)\
        .prefetch_related(
            'lead__authors',
            'lead__authors__organization_type',
            # Also organization parents
            'lead__authors__parent',
            'lead__authors__parent__organization_type',
        )

    search = filters.get('search')
    if search:
        queryset = queryset.filter(
            models.Q(lead__title__icontains=search) |
            models.Q(excerpt__icontains=search)
        )

    filters['project'] = project_id

    exportables = Exportable.objects.filter(
        analysis_framework__project__id=project_id,
        exportdata__isnull=False,
    ).distinct()
    regions = Region.objects.filter(
        project__id=project_id
    ).distinct()

    # which widget data needs to be exported along with
    exporting_widgets = filters.get('exporting_widgets', [])
    report_show_attributes = dict(
        show_lead_entry_id=filters.get('report_show_lead_entry_id', True),
        show_assessment_data=filters.get('report_show_assessment_data', True),
        show_entry_widget_data=filters.get('report_show_entry_widget_data', True),
    )

    if export_type == Export.EXCEL:
        decoupled = filters.get('decoupled', True)
        export_data = ExcelExporter(queryset, decoupled, project_id, is_preview=is_preview)\
            .load_exportables(exportables, regions)\
            .add_entries(queryset)\
            .export()

    elif export_type == Export.REPORT:
        report_structure = filters.get('report_structure')
        report_levels = filters.get('report_levels')
        text_widget_ids = filters.get('text_widget_ids') or []
        show_groups = filters.get('show_groups')
        pdf = export.filters.get('pdf', False)
        export_data = (
            ReportExporter(
                exporting_widgets=exporting_widgets,
                is_preview=is_preview,
                **report_show_attributes,
            ).load_exportables(exportables, regions)
            .load_levels(report_levels)
            .load_structure(report_structure)
            .load_group_lables(queryset, show_groups)
            .load_text_from_text_widgets(queryset, text_widget_ids)
            .add_entries(queryset)
            .export(pdf=pdf)
        )

    elif export_type == Export.JSON:
        export_data = JsonExporter(is_preview=is_preview)\
            .load_exportables(exportables)\
            .add_entries(queryset)\
            .export()

    else:
        raise Exception(
            '(Entries Export) Unkown Export Type Provided: {export_type} for Export: {export.id}'
        )

    return export_data
