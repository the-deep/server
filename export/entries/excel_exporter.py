from django.core.files.base import ContentFile

from export.formats.xlsx import WorkBook, RowsBuilder
from export.mime_types import EXCEL_MIME_TYPE
from entry.models import Entry, ExportData
from geo.models import GeoArea
from utils.common import format_date, generate_filename


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
