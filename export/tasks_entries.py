from celery import shared_task
from django.contrib.auth.models import User
from django.db import models

from analysis_framework.models import Exportable
from entry.filter_set import EntryFilterSet, get_filtered_entries
from export.models import Export
from export.entries import ExcelExporter, ReportExporter
from geo.models import Region

import traceback
import logging

logger = logging.getLogger(__name__)


def _export_entries(export_type, export_id, user_id, project_id, filters):
    user = User.objects.get(id=user_id)
    export = Export.objects.get(id=export_id)

    queryset = get_filtered_entries(user, filters)

    search = filters.get('search')
    if search:
        queryset = queryset.filter(
            models.Q(lead__title__icontains=search) |
            models.Q(excerpt__icontains=search)
        )

    filters['project'] = project_id

    queryset = EntryFilterSet(filters, queryset=queryset).qs

    exportables = Exportable.objects.filter(
        analysis_framework__project__id=project_id
    ).distinct()
    regions = Region.objects.filter(
        project__id=project_id
    ).distinct()

    if export_type == 'excel':
        decoupled = filters.get('decoupled', True)
        ExcelExporter(decoupled)\
            .load_exportables(exportables, regions)\
            .add_entries(queryset)\
            .export(export)

    elif export_type == 'report':
        report_structure = filters.get('report_structure')
        pdf = filters.get('pdf', False)
        ReportExporter()\
            .load_exportables(exportables)\
            .load_structure(report_structure)\
            .add_entries(queryset)\
            .export(export, pdf)

    return True


@shared_task
def export_entries(export_type, export_id, user_id, project_id, filters):
    try:
        return_value = _export_entries(
            export_type,
            export_id,
            user_id,
            project_id,
            filters,
        )
    except Exception as e:
        logger.error(traceback.format_exc())
        return_value = False

    return return_value
