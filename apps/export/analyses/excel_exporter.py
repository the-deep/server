from django.core.files.base import ContentFile

from export.formats.xlsx import WorkBook

import logging

from deep.permalinks import Permalink

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
        # FIXME: Use values only instead of fetching everything.
        qs = analytical_statement_entries.select_related(
            'entry',
            'entry__lead',
            'analytical_statement',
            'analytical_statement__analysis_pillar',
            'analytical_statement__analysis_pillar__assignee',
        )
        for analytical_statement_entry in qs.iterator():
            entry = analytical_statement_entry.entry
            lead = entry.lead
            analytical_statement = analytical_statement_entry.analytical_statement
            analysis_pillar = analytical_statement.analysis_pillar
            self.analysis_sheet.append([[
                analysis_pillar.id,
                analysis_pillar.title,
                analysis_pillar.assignee.get_display_name(),
                analytical_statement.pk,
                analytical_statement.statement,
                entry.id,
                entry.excerpt,
                Permalink.entry(entry.project_id, lead.id, entry.id),
                lead.url,
            ]])
        return self

    def export(self):
        buffer = self.wb.save()
        return ContentFile(buffer)
