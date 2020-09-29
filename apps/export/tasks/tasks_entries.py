from django.db import models

from analysis_framework.models import Exportable
from entry.filter_set import get_filtered_entries
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

    if export_type == Export.EXCEL:
        decoupled = filters.get('decoupled', True)
        export_data = ExcelExporter(queryset, decoupled, project_id)\
            .load_exportables(exportables, regions)\
            .add_entries(queryset)\
            .export()

    elif export_type == Export.REPORT:
        report_structure = filters.get('report_structure')
        report_levels = filters.get('report_levels')
        text_widget_ids = filters.get('text_widget_ids') or []
        show_groups = filters.get('show_groups')
        pdf = export.filters.get('pdf', False)
        export_data = ReportExporter()\
            .load_exportables(exportables)\
            .load_levels(report_levels)\
            .load_structure(report_structure)\
            .load_group_lables(queryset, show_groups)\
            .load_text_from_text_widgets(queryset, text_widget_ids)\
            .add_entries(queryset)\
            .export(pdf=pdf)

    elif export_type == Export.JSON:
        export_data = JsonExporter()\
            .load_exportables(exportables)\
            .add_entries(queryset)\
            .export()

    else:
        raise Exception(
            f'(Entries Export) Unkown Export Type Provided: {export_type} for Export:{export.id}'
        )

    return export_data
