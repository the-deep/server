from django.conf import settings
from django.core.files.base import ContentFile, File
from django.db.models import Case, When, Q

from export.formats.docx import Document
from export.mime_types import (
    DOCX_MIME_TYPE,
    PDF_MIME_TYPE,
)

from entry.models import Entry, ExportData
from lead.models import Lead
from utils.common import generate_filename
from tabular.viz import renderer as viz_renderer
from export.models import Export

from subprocess import call
import os
import tempfile
import logging


logger = logging.getLogger(__name__)


class ReportExporter:
    def __init__(self):
        self.doc = Document(
            os.path.join(settings.APPS_DIR, 'static/doc_export/template.docx')
        )
        self.lead_ids = []

    def load_exportables(self, exportables):
        exportables = exportables.filter(
            data__report__levels__isnull=False,
        )

        self.exportables = exportables
        return self

    def load_structure(self, structure):
        self.structure = structure
        return self

    def _generate_for_entry(self, entry):
        """
        Generate paragraphs for an entry
        """

        # Format is
        # excerpt (source)
        # where source is hyperlinked to appropriate url

        # Excerpt can also be image
        excerpt = (
            entry.excerpt if entry.entry_type == Entry.EXCERPT
            else ''
        )
        para = self.doc.add_paragraph(excerpt).justify()

        # NOTE: Use doc.add_image for limiting image size to page width
        # and run.add_image for actual size image

        image = None
        image_text = None
        if entry.entry_type == Entry.IMAGE:
            image = entry.image
            # para.add_run().add_image(entry.image)
        elif entry.entry_type == Entry.DATA_SERIES and entry.tabular_field:
            image = viz_renderer.get_entry_image(entry)
            h_stats = (entry.tabular_field.cache or {}).get('health_stats', {})

            image_text = ' Total values: {}'.format(h_stats.get('total', 'N/A'))
            for key in ['invalid', 'null']:
                if h_stats.get(key):
                    image_text += f', {key.title()} values: {h_stats.get(key)}' if h_stats.get(key) else ''

        if image:
            self.doc.add_image(image)
            self.doc.add_paragraph(image_text).justify()
            para = self.doc.add_paragraph().justify()

        lead = entry.lead
        self.lead_ids.append(lead.id)

        source = (
            (lead.source and lead.source.data.title) or lead.source_raw or
            'Reference'
        )
        author = (lead.author and lead.author.data.title) or lead.author_raw
        url = lead.url or (
            lead.attachment and lead.attachment.get_file_url()
        )
        date = entry.lead.published_on

        para.add_run(' (')

        (author and author.lower() != (source or '').lower()) and para.add_run(f'{author}, ')
        para.add_hyperlink(url, source) if url else para.add_run(source)
        lead.confidentiality == Lead.CONFIDENTIAL and para.add_run(' (confidential)')
        # TODO: use utils.common.format_date and perhaps use information date
        date and para.add_run(f", {date.strftime('%d/%m/%Y')}")

        para.add_run(')')

        self.doc.add_paragraph()

    def _load_into_levels(
            self,
            entry,
            keys,
            levels,
            entries_map,
            valid_levels,
    ):
        """
        Map an entry into corresponding levels
        """
        parent_level_valid = False
        for level in levels:
            level_id = level.get('id')
            valid_level = (level_id in keys)

            if valid_level:
                if not entries_map.get(level_id):
                    entries_map[level_id] = []
                entries_map[level_id].append(entry)

            sublevels = level.get('sublevels')
            if sublevels:
                valid_level = valid_level or self._load_into_levels(
                    entry,
                    keys,
                    sublevels,
                    entries_map,
                    valid_levels,
                )

            if valid_level and level_id not in valid_levels:
                valid_levels.append(level_id)

            parent_level_valid = parent_level_valid or valid_level
        return parent_level_valid

    def _generate_for_levels(
            self,
            levels,
            level_entries_map,
            valid_levels,
            structures=None,
            heading_level=2,
    ):
        """
        Generate paragraphs for all entries in this level and recursively
        do it for further sublevels
        """
        if structures is not None:
            level_map = dict((level.get('id'), level) for level in levels)
            levels = [level_map[s['id']] for s in structures]

        for level in levels:
            if level.get('id') not in valid_levels:
                continue

            title = level.get('title')
            entries = level_entries_map.get(level.get('id'))
            sublevels = level.get('sublevels')

            if entries or sublevels:
                self.doc.add_heading(title, heading_level)
                self.doc.add_paragraph()

            if entries:
                [self._generate_for_entry(entry) for entry in entries]

            if sublevels:
                substructures = None
                if structures:
                    substructures = next((
                        s.get('levels') for s in structures
                        if s['id'] == level.get('id')
                    ), None)

                self._generate_for_levels(
                    sublevels,
                    level_entries_map,
                    valid_levels,
                    substructures,
                    heading_level + 1,
                )

    def _generate_for_uncategorized(self, entries):
        entries = entries.exclude(
            Q(exportdata__data__report__keys__isnull=False) |
            Q(exportdata__data__report__keys__len__gt=0)
        )
        if entries.count() == 0:
            return

        self.doc.add_heading('Uncategorized', 2)
        self.doc.add_paragraph()

        if entries:
            [self._generate_for_entry(entry) for entry in entries]

    def add_entries(self, entries):
        """
        Add entries and generate parapgraphs for all entries
        """
        exportables = self.exportables
        uncategorized = False

        if self.structure:
            ids = [s['id'] for s in self.structure]
            uncategorized = 'uncategorized' in ids
            ids = [id for id in ids if id != 'uncategorized']

            order = Case(*[
                When(pk=pk, then=pos)
                for pos, pk
                in enumerate(ids)
            ])
            exportables = exportables.filter(pk__in=ids).order_by(order)

        for exportable in exportables:
            levels = exportable.data.get('report').get('levels')

            level_entries_map = {}
            valid_levels = []
            for entry in entries:
                # TODO
                # Set entry.report_data to all exportdata for all exportable
                # for this entry for later use

                export_data = ExportData.objects.filter(
                    entry=entry,
                    exportable=exportable,
                    data__report__keys__isnull=False,
                ).first()

                if export_data:
                    self._load_into_levels(
                        entry, export_data.data.get('report').get('keys'),
                        levels, level_entries_map, valid_levels,
                    )

            structures = self.structure and next((
                s.get('levels') for s in self.structure
                if str(s['id']) == str(exportable.id)
            ), None)
            self._generate_for_levels(levels, level_entries_map,
                                      valid_levels, structures)

        if uncategorized:
            self._generate_for_uncategorized(entries)

        return self

    def export(self, pdf=False):
        """
        Export and return export data
        """

        # Get all leads to generate Bibliography
        lead_ids = list(set(self.lead_ids))
        leads = Lead.objects.filter(id__in=lead_ids)

        self.doc.add_paragraph().add_horizontal_line()
        self.doc.add_paragraph()
        self.doc.add_heading('Bibliography', 1)
        self.doc.add_paragraph()

        for lead in leads:
            # Format is"
            # Source. Title. Date. Url

            para = self.doc.add_paragraph()
            author = (lead.author and lead.author.data.title) or lead.author_raw
            source = (
                (lead.source and lead.source.data.title) or lead.source_raw or
                'Missing source'
            )

            author and para.add_run(f'{author}.')
            para.add_run(f' {source}.')
            para.add_run(f' {lead.title}.')
            lead.published_on and para.add_run(f" {lead.published_on.strftime('%m/%d/%y')}. ")

            para = self.doc.add_paragraph()
            url = lead.url or (
                lead.attachment and lead.attachment.get_file_url()
            )
            if url:
                para.add_hyperlink(url, url)
            else:
                para.add_run('Missing url.')

            if lead.confidentiality == Lead.CONFIDENTIAL:
                para.add_run(' (confidential)')

            self.doc.add_paragraph()
        self.doc.add_page_break()

        if pdf:
            temp_doc = tempfile.NamedTemporaryFile(dir=settings.TEMP_DIR)
            self.doc.save_to_file(temp_doc)

            filename = temp_doc.name.split('/')[-1]
            temp_pdf = os.path.join(settings.TEMP_DIR,
                                    '{}.pdf'.format(filename))

            call(['libreoffice', '--headless', '--convert-to',
                  'pdf', temp_doc.name, '--outdir', settings.TEMP_DIR])

            filename = generate_filename('Entries General Export', 'pdf')
            file = File(open(temp_pdf, 'rb'))
            export_format = Export.PDF
            export_mime_type = PDF_MIME_TYPE

            # Cleanup
            os.unlink(temp_pdf)
            temp_doc.close()

        else:
            buffer = self.doc.save()

            filename = generate_filename('Entries General Export', 'docx')
            file = ContentFile(buffer)
            export_format = Export.DOCX
            export_mime_type = DOCX_MIME_TYPE

        return filename, export_format, export_mime_type, file
