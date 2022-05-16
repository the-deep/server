from django.core.files.base import ContentFile
from django.conf import settings

from export.formats.xlsx import WorkBook

import logging

logger = logging.getLogger('__name__')


class ExcelExporter:
    def __init__(self, analytical_statement_entries):
        self.wb = WorkBook()
        self.split = None
        self.analysis_sheet = self.wb.get_active_sheet().set_title('Analysis')

        self.titles = [
            'Analysis Pillar ID',
            'Analysis Pillar',
            'Assignee',
            'Statement ID',
            'Statement',
            'Entry ID',
            'Entry',
            'Entry Link',
            'Source Link'
        ]

    def add_analytical_statement_entries(self, analytical_statement_entries):
        self.analysis_sheet.append([self.titles])
        for analytical_statement_entry in analytical_statement_entries:
            url = f'{settings.HTTP_PROTOCOL}://{settings.DEEPER_FRONTEND_HOST}/permalink/projects/'
            f'{analytical_statement_entry.entry.project_id}/leads/{analytical_statement_entry.entry.lead_id}/'
            f'entries/{analytical_statement_entry.entry.id}/'
            self.analysis_sheet.append([[
                analytical_statement_entry.analytical_statement.analysis_pillar_id,
                analytical_statement_entry.analytical_statement.analysis_pillar.title,
                analytical_statement_entry.analytical_statement.analysis_pillar.assignee.get_display_name(),
                analytical_statement_entry.analytical_statement_id,
                analytical_statement_entry.analytical_statement.statement,
                analytical_statement_entry.entry_id,
                analytical_statement_entry.entry.excerpt,
                url,
                analytical_statement_entry.entry.lead.url,

            ]])
        return self

    def export(self):
        buffer = self.wb.save()
        return ContentFile(buffer)
