from django.db import models

from analysis_framework.models import Exportable
from entry.filter_set import EntryFilterSet, get_filtered_entries
from entry.models import Entry
from export.models import Export
from export.entries.excel_exporter import ExcelExporter
from export.entries.report_exporter import ReportExporter
from export.entries.json_exporter import JsonExporter
from geo.models import Region


def export_entries(export):
    user = export.exported_by
    project_id = export.project.id
    export_type = export.export_type
    is_preview = export.is_preview

    filters = export.filters
    queryset = get_filtered_entries(user, filters).prefetch_related(
        'entrygrouplabel_set'
    )
    queryset = Entry.get_exportable_queryset(queryset)

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

    if export_type == Export.EXCEL:
        decoupled = filters.get('decoupled', True)
        export_data = ExcelExporter(queryset, decoupled, project_id)\
            .load_exportables(exportables, regions)\
            .add_entries(queryset, is_preview)\
            .export(is_preview)

    elif export_type == Export.REPORT:
        report_structure = filters.get('report_structure')
        report_levels = filters.get('report_levels')
        text_widget_ids = filters.get('text_widget_ids') or []
        show_groups = filters.get('show_groups')
        pdf = export.filters.get('pdf', False)
        export_data = ReportExporter(exporting_widgets=exporting_widgets)\
            .load_exportables(exportables, regions)\
            .load_levels(report_levels)\
            .load_structure(report_structure)\
            .load_group_lables(queryset, show_groups)\
            .load_text_from_text_widgets(queryset, text_widget_ids)\
            .add_entries(queryset, is_preview)\
            .export(is_preview, pdf=pdf)

    elif export_type == Export.JSON:
        export_data = JsonExporter()\
            .load_exportables(exportables)\
            .add_entries(queryset, is_preview)\
            .export(is_preview)

    else:
        raise Exception('(Entries Export) Unkown Export Type Provided: {} for Export:'.format(export_type, export.id))

    return export_data
