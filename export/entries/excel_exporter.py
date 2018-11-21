from django.core.files.base import ContentFile

from export.formats.xlsx import WorkBook, RowsBuilder
from export.mime_types import EXCEL_MIME_TYPE
from entry.models import Entry, ExportData
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

        self.region_data = {}

    def load_exportable_titles(self, data, regions):
        export_type = data.get('type')

        if export_type == 'nested':
            children = data.get('children')
            for child in children:
                self.load_exportable_titles(child, regions)

        elif export_type == 'geo' and regions:
            self.region_data = {}

            for region in regions:
                admin_levels = region.adminlevel_set.all()
                admin_level_data = []

                for admin_level in admin_levels:
                    self.titles.append(admin_level.title)

                    # Collect geo area names for each admin level
                    if not admin_level.geo_area_titles:
                        admin_level.calc_cache()
                    admin_level_data.append({
                        'id': admin_level.id,
                        'geo_area_titles': admin_level.geo_area_titles,
                    })

                self.region_data[region.id] = admin_level_data

        elif export_type == 'multiple':
            self.titles.extend(data.get('titles'))

        elif data.get('title'):
            self.titles.append(data.get('title'))

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
            self.load_exportable_titles(data, regions)

        if self.decoupled and self.split:
            self.split.append([self.titles])
        self.group.append([self.titles])

        if self.decoupled and self.split:
            self.split.auto_fit_cells_in_row(1)
        self.group.auto_fit_cells_in_row(1)

        self.exportables = exportables
        self.regions = regions
        return self

    def add_entries_from_excel_data(self, rows, data, export_data):
        export_type = data.get('type')

        if export_type == 'nested':
            children = data.get('children')
            if export_data:
                for i, child in enumerate(children):
                    self.add_entries_from_excel_data(
                        rows,
                        child,
                        export_data[i],
                    )

        elif export_type == 'multiple':
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
                values = [str(v) for v in values]

            for region in self.regions:
                admin_levels = self.region_data[region.id]
                for admin_level in admin_levels:
                    geo_area_titles = admin_level['geo_area_titles']
                    selected_titles = [
                        geo_area_titles[geo_id]
                        for geo_id in values
                        if geo_id in geo_area_titles
                    ]
                    if len(selected_titles) > 0:
                        rows.add_rows_of_values(selected_titles)
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

    def add_entries(self, entries):
        for entry in entries:
            # Export each entry
            # Start building rows and export data for each exportable

            rows = RowsBuilder(self.split, self.group, self.decoupled)
            rows.add_value(format_date(entry.lead.published_on))

            assignee = entry.lead.get_assignee()
            rows.add_value_list([
                entry.created_by.profile.get_display_name(),
                format_date(entry.created_at.date()),
                entry.lead.title,
                entry.lead.source,
                assignee and assignee.profile.get_display_name(),
                entry.excerpt
                if entry.entry_type == Entry.EXCERPT
                else 'IMAGE',
            ])

            for exportable in self.exportables:
                # Get export data for this entry corresponding to this
                # exportable.

                # And write some value based on type and data
                # or empty strings if no data.

                data = exportable.data.get('excel')
                export_data = ExportData.objects.filter(
                    exportable=exportable,
                    entry=entry,
                    data__excel__isnull=False,
                ).first()

                export_data = export_data and export_data.data.get('excel')
                self.add_entries_from_excel_data(rows, data, export_data)

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
