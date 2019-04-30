import logging
from django.core.files.base import ContentFile

from export.formats.xlsx import WorkBook, RowsBuilder
from export.mime_types import EXCEL_MIME_TYPE
from entry.models import Entry, ExportData
from utils.common import format_date, generate_filename, excel_column_name

logger = logging.getLogger(__name__)


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

        self.col_types = {
            0: 'date',
            2: 'date',
        }

        # Keep track of sheet data present
        '''
        tabular_sheets = {
            'leadtitle-sheettitle': {
                'field1_title': col_num_in_sheet,
                'field2_title': col_num_in_sheet,
            }
        }
        '''
        self.tabular_sheets = {}

        # Keep track of tabular fields
        self.tabular_fields = {}

        self.region_data = {}

    def load_exportable_titles(self, data, regions):
        export_type = data.get('type')
        col_type = data.get('col_type')

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
                    self.titles.append('{} (code)'.format(admin_level.title))

                    # Collect geo area names for each admin level
                    if not admin_level.geo_area_titles:
                        admin_level.calc_cache()
                    admin_level_data.append({
                        'id': admin_level.id,
                        'geo_area_titles': admin_level.geo_area_titles,
                    })

                self.region_data[region.id] = admin_level_data

        elif export_type == 'multiple':
            index = len(self.titles)
            self.titles.extend(data.get('titles'))
            if col_type:
                for i in range(index, len(self.titles)):
                    self.col_types[i] = col_type[i - index]

        elif data.get('title'):
            index = len(self.titles)
            self.titles.append(data.get('title'))
            if col_type:
                self.col_types[index] = col_type

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
                    if i >= len(export_data):
                        continue
                    self.add_entries_from_excel_data(
                        rows,
                        child,
                        export_data[i],
                    )

        elif export_type == 'multiple':
            col_span = len(data.get('titles'))
            if export_data:
                if export_data.get('type') == 'lists':
                    export_data_values = export_data.get('values')
                    rows_of_value_lists = []
                    for export_data_value in export_data_values:
                        # Handle for Matrix2D subsectors
                        if len(export_data_value) == 4 and isinstance(export_data_value[3], list):
                            if len(export_data_value[3]) > 0:
                                for subsector in export_data_value[3]:
                                    rows_of_value_lists.append(export_data_value[:3] + [subsector])
                            else:
                                rows_of_value_lists.append(export_data_value[:3] + [''])
                        else:
                            rows_of_value_lists.append(export_data_value)
                    rows.add_rows_of_value_lists(
                        # Filter if all values are None
                        [
                            x for x in rows_of_value_lists
                            if not all(y is None for y in x)
                        ],
                        col_span,
                    )
                else:
                    rows.add_value_list(
                        # Filter if all values are None
                        [
                            x for x in export_data.get('values')
                            if not all(y is None for y in x)
                        ],
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
                max_levels = len(admin_levels)
                rows_value = []
                for rev_level, admin_level in enumerate(admin_levels[::-1]):
                    geo_area_titles = admin_level['geo_area_titles']
                    level = max_levels - rev_level
                    for geo_id in values:
                        if geo_id not in geo_area_titles:
                            continue
                        row_values = ['' for i in range(0, max_levels - level)] * 2

                        title = geo_area_titles[geo_id].get('title', '')
                        code = geo_area_titles[geo_id].get('code', '')
                        parent_id = geo_area_titles[geo_id].get('parent_id')

                        row_values.extend([code, title])
                        for _level in range(0, level - 1)[::-1]:
                            if parent_id:
                                _geo_area_titles = admin_levels[_level]['geo_area_titles']
                                _geo_area = _geo_area_titles.get(parent_id) or {}
                                _title = _geo_area.get('title', '')
                                _code = _geo_area.get('code', '')
                                parent_id = _geo_area.get('parent_id')
                                row_values.extend([_code, _title])
                            else:
                                row_values.extend(['', ''])
                        rows_value.append(row_values[::-1])
                rows.add_rows_of_value_lists(rows_value)
        else:
            if export_data:
                if export_data.get('type') == 'list':
                    rows.add_rows_of_values(
                        # This is in hope of filtering out non-existent data from excel row
                        [
                            x for x in export_data.get('value', [])
                            if x is not None
                        ]
                    )
                else:
                    rows.add_value(export_data.get('value'))
            else:
                rows.add_value('')

    def get_data_series(self, entry):
        lead = entry.lead
        field = entry.tabular_field

        if field is None:
            return ''
        self.tabular_fields[field.id] = field

        # Get Sheet title which is Lead title - Sheet title
        # Worksheet title is limited to 31 as excel's tab length is capped to 31
        worksheet_title = '{}-{}'.format(lead.title, field.sheet.title)
        if len(worksheet_title) > 31:
            worksheet_title = '{}-{}'.format(
                worksheet_title[:28],
                len(self.wb.wb.worksheets)
            )

        if worksheet_title not in self.wb.wb.sheetnames:
            tabular_sheet = self.wb.create_sheet(worksheet_title).ws
        else:
            tabular_sheet = self.wb.wb.get_sheet_by_name(worksheet_title)

        # Get fields data
        worksheet_data = self.tabular_sheets.get(worksheet_title, {})

        col_number = worksheet_data.get(field.title)
        if col_number is None:
            # col_number None means we don't have the field in the work sheet
            # So, we create one assigning next number to the field
            cols_count = len(worksheet_data.keys())
            col_number = cols_count + 1
            worksheet_data[field.title] = col_number

            # Now add data to the column
            # excel_column_name converts number to excel column names: 1 -> A..
            sheet_col_name = excel_column_name(col_number)

            self.tabular_sheets[worksheet_title] = worksheet_data

            # Insert field title to sheet in first row
            tabular_sheet['{}1'.format(sheet_col_name)].value =\
                field.title

            # Add field values to corresponding column
            for i, x in enumerate(field.data):
                tabular_sheet[
                    '{}{}'.format(sheet_col_name, 2 + i)
                ].value = x.get('processed_value') or x['value']
        else:
            sheet_col_name = excel_column_name(col_number)

        return "='{}'!{}1".format(worksheet_title, sheet_col_name)

    def get_entry_data(self, entry):
        if entry.entry_type == Entry.EXCERPT:
            return entry.excerpt

        if entry.entry_type == Entry.IMAGE:
            return entry.get_shareable_image_url()

        if entry.entry_type == Entry.DATA_SERIES:
            try:
                return self.get_data_series(entry)
            except Exception:
                logger.error(
                    'Data Series EXCEL Export Failed for entry',
                    exc_info=1,
                    extra={'entry_id': entry.pk},
                )

        return ''

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
                self.get_entry_data(entry),
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
        self.group.set_col_types(self.col_types)
        if self.split:
            self.split.set_col_types(self.col_types)

        buffer = self.wb.save()
        filename = generate_filename('Entries Export', 'xlsx')

        export_entity.title = filename
        export_entity.type = 'entries'
        export_entity.format = 'xlsx'
        export_entity.pending = False
        export_entity.mime_type = EXCEL_MIME_TYPE

        export_entity.file.save(filename, ContentFile(buffer))
        export_entity.save()
