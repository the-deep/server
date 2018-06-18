from django.conf import settings
from django.core.files.base import ContentFile, File
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Case, When

from export.formats.xlsx import WorkBook, RowsBuilder
from export.formats.docx import Document

from analysis_framework.models import Widget
from entry.models import Entry, ExportData
from lead.models import Lead
from geo.models import GeoArea
from utils.common import format_date, generate_filename
from export.models import Export

from subprocess import call
import os
import tempfile
import json


DOCX_MIME_TYPE = \
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
PDF_MIME_TYPE = \
    'application/pdf'
EXCEL_MIME_TYPE = \
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
JSON_MIME_TYPE = \
    'application/json'


class ExcelExporter:
    def __init__(self, decoupled=True):
        self.wb = WorkBook()

        # Create two worksheets
        if decoupled:
            self.split = self.wb.get_active_sheet()\
                .set_title('Split Entries')
            self.group = self.wb.create_sheet('Grouped Entries')
        else:
            self.split = None
            self.group = self.wb.get_active_sheet().set_title('Entries')
        self.decoupled = decoupled

        # Initial titles
        self.titles = [
            'Date of Lead Publication',
            'Imported By',
            'Date Imported',
            'Lead Title',
            'Source',
            'Assignee',
            'Excerpt',
        ]

    def load_exportables(self, exportables, regions=None):
        # Take all exportables that contains excel info
        exportables = exportables.filter(
            data__excel__isnull=False,
        )

        # information_date_index = 1
        for exportable in exportables:
            # For each exportable, create titles according to type
            # and data

            data = exportable.data.get('excel')
            export_type = data.get('type')

            # if export_type == 'information-date':
            #     self.titles.insert(
            #         information_date_index,
            #         data.get('title'),
            #     )
            #     information_date_index += 1

            if export_type == 'geo' and regions:
                for region in regions:
                    admin_levels = region.adminlevel_set.all()
                    for admin_level in admin_levels:
                        self.titles.append(admin_level.title)

            elif export_type == 'multiple':
                self.titles.extend(data.get('titles'))

            elif data.get('title'):
                self.titles.append(data.get('title'))

        if self.decoupled and self.split:
            self.split.append([self.titles])
        self.group.append([self.titles])

        if self.decoupled and self.split:
            self.split.auto_fit_cells_in_row(1)
        self.group.auto_fit_cells_in_row(1)

        self.exportables = exportables
        self.regions = regions
        return self

    def add_entries(self, entries):
        for entry in entries:
            # Export each entry
            # Start building rows and export data for each exportable

            rows = RowsBuilder(self.split, self.group, self.decoupled)
            rows.add_value(format_date(entry.lead.published_on))

            # TODO Check for information dates

            rows.add_value_list([
                entry.created_by.profile.get_display_name(),
                format_date(entry.created_at.date()),
                entry.lead.title,
                entry.lead.source,
                entry.lead.get_assignee(),
                entry.excerpt
                if entry.entry_type == Entry.EXCERPT
                else 'IMAGE',
            ])

            for exportable in self.exportables:
                # Get export data for this entry corresponding to this
                # exportable

                # And write some value based on type and data
                # or empty strings if no data

                data = exportable.data.get('excel')
                export_data = ExportData.objects.filter(
                    exportable=exportable,
                    entry=entry,
                    data__excel__isnull=False,
                ).first()

                export_data = export_data and export_data.data.get('excel')
                export_type = data.get('type')

                if export_type == 'multiple':
                    col_span = len(data.get('titles'))
                    if export_data:
                        if export_data.get('type') == 'lists':
                            rows.add_rows_of_value_lists(
                                export_data.get('values'),
                                col_span,
                            )
                        else:
                            rows.add_value_list(
                                export_data.get('values'),
                            )
                    else:
                        rows.add_value_list([''] * col_span)

                elif export_type == 'geo' and self.regions:
                    values = []
                    if export_data:
                        values = export_data.get('values', [])
                        values = [int(v) for v in values]

                    for region in self.regions:
                        admin_levels = region.adminlevel_set.all()

                        for admin_level in admin_levels:
                            geo_data = GeoArea.objects.filter(
                                admin_level=admin_level,
                                id__in=values,
                            ).distinct()
                            if geo_data.count() > 0:
                                rows.add_rows_of_values([
                                    g.title for g in geo_data
                                ])
                            else:
                                rows.add_value('')

                else:
                    if export_data:
                        if export_data.get('type') == 'list':
                            rows.add_rows_of_values(export_data.get('value'))
                        else:
                            rows.add_value(export_data.get('value'))
                    else:
                        rows.add_value('')

            rows.apply()
        return self

    def export(self, export_entity):
        buffer = self.wb.save()
        filename = generate_filename('Entries Export', 'xlsx')

        export_entity.title = filename
        export_entity.type = 'entries'
        export_entity.format = 'xlsx'
        export_entity.pending = False
        export_entity.mime_type = EXCEL_MIME_TYPE

        export_entity.file.save(filename, ContentFile(buffer))
        export_entity.save()


class ReportExporter:
    def __init__(self):
        self.doc = Document(
            os.path.join(settings.BASE_DIR, 'static/doc_export/template.docx')
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

        if entry.entry_type == Entry.IMAGE:
            self.doc.add_image(entry.image)
            # para.add_run().add_image(entry.image)

        lead = entry.lead
        self.lead_ids.append(lead.id)

        source = lead.source or 'Reference'
        url = lead.url or (
            lead.attachment and lead.attachment.file and
            lead.attachment.file.url
        )

        # TODO Information Date: ', {}'.format(info_date)

        para.add_run(' (')
        if url:
            para.add_hyperlink(url, source)
        else:
            para.add_run(source)

        date = entry.lead.published_on
        if date:
            para.add_run(', {}'.format(date.strftime('%d/%m/%Y')))

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

    def add_entries(self, entries):
        """
        Add entries and generate parapgraphs for all entries
        """
        exportables = self.exportables

        if self.structure:
            ids = [s['id'] for s in self.structure]
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
                if s['id'] == exportable.id
            ), None)
            self._generate_for_levels(levels, level_entries_map,
                                      valid_levels, structures)

        return self

    def export(self, export_entity, pdf=False):
        """
        Export and save in export_entity
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
            if lead.source and lead.source != '':
                para.add_run('{}.'.format(lead.source.title()))
            else:
                para.add_run('Missing source.')

            para.add_run(' {}.'.format(lead.title.title()))
            if lead.published_on:
                para.add_run(' {}.'.format(
                    lead.published_on.strftime('%m/%d/%y')
                ))

            para = self.doc.add_paragraph()
            url = lead.url or (
                lead.attachment and lead.attachment.file and
                lead.attachment.file.url
            )
            if url:
                para.add_hyperlink(url, url)
            else:
                para.add_run('Missing url.')

            self.doc.add_paragraph()
        self.doc.add_page_break()

        if pdf:
            temp_doc = tempfile.NamedTemporaryFile(dir=settings.BASE_DIR)
            self.doc.save_to_file(temp_doc)

            filename = temp_doc.name.split('/')[-1]
            temp_pdf = os.path.join(settings.BASE_DIR,
                                    '{}.pdf'.format(filename))

            call(['libreoffice', '--headless', '--convert-to',
                  'pdf', temp_doc.name, '--outdir', settings.BASE_DIR])

            filename = generate_filename('Entries General Export', 'pdf')
            export_entity.file.save(filename, File(open(temp_pdf, 'rb')))

            os.unlink(temp_pdf)
            temp_doc.close()

            export_entity.format = Export.PDF
            export_entity.mime_type = PDF_MIME_TYPE
        else:
            buffer = self.doc.save()
            filename = generate_filename('Entries General Export', 'docx')
            export_entity.file.save(filename, ContentFile(buffer))

            export_entity.format = Export.DOCX
            export_entity.mime_type = DOCX_MIME_TYPE

        export_entity.title = filename
        export_entity.type = Export.ENTRIES
        export_entity.pending = False

        export_entity.save()


class JsonExporter:
    def __init__(self):
        self.data = {}

    def load_exportables(self, exportables):
        self.exportables = exportables
        self.widget_ids = []

        self.data['widgets'] = []
        for exportable in self.exportables:
            widget = Widget.objects.get(
                analysis_framework=exportable.analysis_framework,
                key=exportable.widget_key,
            )
            self.widget_ids.append(widget.id)

            data = {}
            data['id'] = widget.key
            data['widget_type'] = widget.widget_id
            data['title'] = widget.title
            data['properties'] = widget.properties
            self.data['widgets'].append(data)

        return self

    def add_entries(self, entries):
        self.data['entries'] = []
        for entry in entries:
            data = {}
            data['id'] = entry.id
            data['lead_id'] = entry.lead.id
            data['lead'] = entry.lead.title
            data['source'] = entry.lead.source
            data['date'] = entry.lead.published_on
            data['excerpt'] = entry.excerpt
            data['image'] = entry.image
            data['attributes'] = []

            for attribute in entry.attribute_set.all():
                attribute_data = {}
                attribute_data['widget_id'] = attribute.widget.key
                attribute_data['data'] = attribute.data
                data['attributes'].append(attribute_data)
            self.data['entries'].append(data)
        return self

    def export(self, export_entity):
        """
        Export and save in export_entity
        """
        filename = generate_filename('Entries JSON Export', 'json')
        export_entity.file.save(filename, ContentFile(
            json.dumps(self.data, sort_keys=True, indent=2,
                       cls=DjangoJSONEncoder)
        ))

        export_entity.format = Export.JSON
        export_entity.mime_type = JSON_MIME_TYPE

        export_entity.title = filename
        export_entity.type = Export.ENTRIES
        export_entity.pending = False

        export_entity.save()
