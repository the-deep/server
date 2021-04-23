import logging
from django.core.files.base import ContentFile

from export.formats.xlsx import WorkBook, RowsBuilder
from export.mime_types import EXCEL_MIME_TYPE
from entry.models import Entry, ExportData, ProjectEntryLabel, LeadEntryGroup
from lead.models import Lead
from export.models import Export

from utils.common import (
    format_date,
    generate_filename,
    excel_column_name,
    get_valid_xml_string as xstr
)

logger = logging.getLogger(__name__)

EXPORT_DATE_FORMAT = '%m/%d/%y'


def get_hyperlink(url, text):
    clean_text = xstr(text.replace('"', '""'))
    return f'=HYPERLINK("{url}", "{clean_text}")'


class ExcelExporter:
    def __init__(self, entries, decoupled=True, project_id=None, is_preview=False):
        self.is_preview = is_preview
        self.wb = WorkBook()
        # XXX: Limit memory usage? (Or use redis?)
        self.geoarea_data_cache = {}

        # Create worksheets(Main, Grouped, Entry Groups, Bibliography)
        if decoupled:
            self.split = self.wb.get_active_sheet()\
                .set_title('Split Entries')
            self.group = self.wb.create_sheet('Grouped Entries')
        else:
            self.split = None
            self.group = self.wb.get_active_sheet().set_title('Entries')

        self.entry_groups_sheet = self.wb.create_sheet('Entry Groups')
        self.decoupled = decoupled
        self.bibliography_sheet = self.wb.create_sheet('Bibliography')
        self.bibliography_data = {}

        self.modified_exceprt_exists = entries.filter(
            dropped_excerpt__isnull=False).exclude(dropped_excerpt__exact='').exists()

        # Initial titles
        self.titles = [
            'Date of Lead Publication',
            'Imported By',
            'Date Imported',
            'Verification Status',
            'Lead Id',
            'Lead Title',
            'Lead URL',
            'Author',
            'Source',
            'Lead Priority',
            'Assignee',
            'Entry Id',
            'Lead-Entry Id',
            *(
                [
                    'Modified Excerpt',
                    'Original Excerpt',
                ] if self.modified_exceprt_exists else
                ['Excerpt']
            )
        ]

        self.lead_id_titles_map = {x.id: x.title for x in Lead.objects.filter(project_id=project_id)}

        project_entry_labels = ProjectEntryLabel.objects.filter(
            project_id=project_id
        ).order_by('order')

        self.label_id_title_map = {x.id: x.title for x in project_entry_labels}

        lead_groups = LeadEntryGroup.objects.filter(lead__project_id=project_id).order_by('order')
        self.group_id_title_map = {x.id: x.title for x in lead_groups}
        # Create matrix of labels and groups

        self.group_label_matrix = {
            (group.lead_id, group.id): {x.id: None for x in project_entry_labels}
            for group in lead_groups
        }

        self.entry_group_titles = [
            'Lead',
            'Group',
            *self.label_id_title_map.values(),
        ]
        self.entry_groups_sheet.append([self.entry_group_titles])

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
        # mapping of original name vs truncated name
        self._sheets = {}

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

                self.titles.append(f'{region.title} Polygons')
                for admin_level in admin_levels:
                    self.titles.append(admin_level.title)
                    self.titles.append('{} (code)'.format(admin_level.title))

                    # Collect geo area names for each admin level
                    admin_level_data.append({
                        'id': admin_level.id,
                        'geo_area_titles': admin_level.get_geo_area_titles(),
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
                        # eg: ['dimension', 'subdimension', 'sector', ['sub-sector1', 'sub-sector2']]
                        #       -> ['dimension', 'subdimension', 'sector', 'sub-sector1']
                        #       -> ['dimension', 'subdimension', 'sector', 'sub-sector2']
                        if len(export_data_value) == 4 and isinstance(export_data_value[3], list):
                            if len(export_data_value[3]) > 0:
                                for subsector in export_data_value[3]:
                                    rows_of_value_lists.append(export_data_value[:3] + [subsector])
                            else:
                                rows_of_value_lists.append(export_data_value[:3] + [''])
                        elif len(export_data_value) != len(data.get('titles')):
                            titles_len = len(data.get('titles'))
                            values_len = len(export_data_value)
                            if titles_len > values_len:
                                # Add additional empty cells
                                rows_of_value_lists.append(export_data_value + [''] * (titles_len - values_len))
                            else:
                                # Remove extra cells
                                rows_of_value_lists.append(export_data_value[:titles_len])
                        else:
                            rows_of_value_lists.append(export_data_value)
                    rows.add_rows_of_value_lists(
                        # Filter if all values are None
                        [
                            x for x in rows_of_value_lists
                            if x is not None and not all(y is None for y in x)
                        ],
                        col_span,
                    )
                else:
                    rows.add_value_list(export_data.get('values'))
            else:
                rows.add_value_list([''] * col_span)

        elif export_type == 'geo' and self.regions:
            geo_id_values = []
            region_geo_polygons = {}
            if export_data:
                geo_id_values = [str(v) for v in export_data.get('values') or []]
                for geo_polygon in export_data.get('polygons') or []:
                    region_id = geo_polygon['region_id']
                    region_geo_polygons[region_id] = region_geo_polygons.get(region_id) or []
                    region_geo_polygons[region_id].append(geo_polygon['title'])

            for region in self.regions:
                admin_levels = self.region_data[region.id]
                geo_polygons = region_geo_polygons.get(region.id, [])
                max_levels = len(admin_levels)
                rows_value = []

                rows.add_rows_of_values(geo_polygons)

                for rev_level, admin_level in enumerate(admin_levels[::-1]):
                    geo_area_titles = admin_level['geo_area_titles']
                    level = max_levels - rev_level
                    for geo_id in geo_id_values:
                        if geo_id not in geo_area_titles:
                            continue
                        if geo_id in self.geoarea_data_cache:
                            rows_value.append(self.geoarea_data_cache[geo_id])
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
                        self.geoarea_data_cache[geo_id] = row_values[::-1]

                if len(rows_value) > 0:
                    rows.add_rows_of_value_lists(rows_value)
                else:
                    rows.add_rows_of_value_lists([['' for i in range(0, max_levels)] * 2])

        else:
            if export_data:
                if export_data.get('type') == 'list':
                    row_values = [
                        # This is in hope of filtering out non-existent data from excel row
                        x for x in export_data.get('value', [])
                        if x is not None
                    ]
                    rows.add_rows_of_values(row_values if row_values else [''])
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
        if not self._sheets.get(worksheet_title) and len(worksheet_title) > 31:
            self._sheets[worksheet_title] = '{}-{}'.format(
                worksheet_title[:28],
                len(self.wb.wb.worksheets)
            )
        elif not self._sheets.get(worksheet_title):
            self._sheets[worksheet_title] = worksheet_title
        worksheet_title = self._sheets[worksheet_title]

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
            for i, x in enumerate(field.actual_data):
                tabular_sheet[
                    '{}{}'.format(sheet_col_name, 2 + i)
                ].value = x.get('processed_value') or x['value']
        else:
            sheet_col_name = excel_column_name(col_number)

        link = f'#\'{worksheet_title}\'!{sheet_col_name}1'
        return get_hyperlink(link, field.title)

    def get_entry_data(self, entry):
        if entry.entry_type == Entry.EXCERPT:
            return entry.excerpt

        if entry.entry_type == Entry.IMAGE:
            return entry.get_image_url()

        if entry.entry_type == Entry.DATA_SERIES:
            try:
                return self.get_data_series(entry)
            except Exception:
                logger.error(
                    'Data Series EXCEL Export Failed for entry',
                    exc_info=1,
                    extra={'data': {'entry_id': entry.pk}},
                )

        return ''

    def add_entries(self, entries):
        iterable_entries = entries[:Export.PREVIEW_ENTRY_SIZE] if self.is_preview else entries
        for i, entry in enumerate(iterable_entries):
            # Export each entry
            # Start building rows and export data for each exportable

            # ENTRY GROUP
            # Add it to appropriate row/column in self.group_label_matrix
            for group_label in entry.entrygrouplabel_set.all():
                key = (group_label.group.lead_id, group_label.group_id)
                entries_sheet_name = 'Grouped Entries' if self.decoupled else 'Entries'
                link = f'#\'{entries_sheet_name}\'!A{i+2}'
                self.group_label_matrix[key][group_label.label_id] = get_hyperlink(link, entry.excerpt[:50])

            lead = entry.lead
            assignee = entry.lead.get_assignee()

            author = lead.get_authors_display()
            source = lead.get_source_display()
            published_on = (lead.published_on and lead.published_on.strftime(EXPORT_DATE_FORMAT)) or ''
            url = lead.url

            self.bibliography_data[lead.id] = (author, source, published_on, url, lead.title)

            rows = RowsBuilder(self.split, self.group, self.decoupled)
            rows.add_value(format_date(lead.published_on))

            rows.add_value_list([
                entry.created_by.profile.get_display_name(),
                format_date(entry.created_at.date()),
                'Verified' if entry.verified else 'Unverified',
                f'{lead.id}',
                lead.title,
                lead.url or (lead.attachment and lead.attachment.get_file_url()),
                lead.get_authors_display(),
                lead.get_source_display(),
                lead.get_priority_display(),
                assignee and assignee.profile.get_display_name(),
                f'{entry.id}',
                f'{lead.id}-{entry.id}',
                *(
                    [
                        self.get_entry_data(entry),
                        entry.dropped_excerpt or '',
                    ] if self.modified_exceprt_exists else
                    [self.get_entry_data(entry)]
                )
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

                # TODO: handle for conditional widget
                if export_data and type(export_data.data.get('excel', {})) == list:
                    export_data = export_data.data.get('excel', [])
                else:
                    export_data = export_data and {
                        **export_data.data.get('common', {}),
                        **export_data.data.get('excel', {})
                    }
                self.add_entries_from_excel_data(rows, data, export_data)

            rows.apply()

        # Now add data to entry group sheet
        for (leadid, gid), labeldata in self.group_label_matrix.items():
            row_data = [
                self.lead_id_titles_map.get(leadid), self.group_id_title_map.get(gid),
                *labeldata.values()
            ]
            self.entry_groups_sheet.append([row_data])
        return self

    def add_bibliography_sheet(self):
        self.bibliography_sheet.append([['Author', 'Source', 'Published Date', 'Title']])
        for author, source, published, url, title in self.bibliography_data.values():
            self.bibliography_sheet.append(
                [[author, source, published, get_hyperlink(url, title) if url else title]]
            )

    def export(self):
        """
        Export and return export data
        """
        self.group.set_col_types(self.col_types)
        if self.split:
            self.split.set_col_types(self.col_types)

        # Add bibliography
        self.add_bibliography_sheet()

        buffer = self.wb.save()
        filename = generate_filename('Entries Export', 'xlsx')
        return filename, Export.XLSX, EXCEL_MIME_TYPE, ContentFile(buffer)
