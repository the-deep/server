import logging
from django.core.files.base import ContentFile
from django.db import models

from deep.permalinks import Permalink
from utils.common import (
    excel_column_name,
    get_valid_xml_string as xstr,
    deep_date_parse,
)
from export.formats.xlsx import WorkBook, RowsBuilder

from analysis_framework.models import Widget
from entry.models import Entry, ExportData, ProjectEntryLabel, LeadEntryGroup
from lead.models import Lead
from export.models import Export

logger = logging.getLogger(__name__)


def get_hyperlink(url, text):
    clean_text = xstr(text.replace('"', '""'))
    return f'=HYPERLINK("{url}", "{clean_text}")'


class ExcelExporter:
    class ColumnsData:
        TITLES = {
            **{
                key: label
                for key, label in Export.StaticColumn.choices
            },
            # Override labels here.
            Export.StaticColumn.ENTRY_EXCERPT: lambda self: [
                'Modified Excerpt', 'Original Excerpt'
            ] if self.modified_excerpt_exists else ['Excerpt'],
        }

    def __init__(
        self,
        export_object,
        entries,
        project,
        date_format,
        columns=None,
        decoupled=True,
        is_preview=False,
    ):
        self.project = project
        self.export_object = export_object
        self.is_preview = is_preview
        self.wb = WorkBook()
        # XXX: Limit memory usage? (Or use redis?)
        self.geoarea_data_cache = {}

        # Date Format
        self.date_renderer = Export.get_date_renderer(date_format)

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
        self.columns = columns
        self.bibliography_sheet = self.wb.create_sheet('Bibliography')

        self.modified_excerpt_exists = entries.filter(excerpt_modified=True).exists()

        project_entry_labels = ProjectEntryLabel.objects.filter(
            project=self.project,
        ).order_by('order')

        self.label_id_title_map = {
            _id: title for _id, title in project_entry_labels.values_list('id', 'title')
        }

        lead_groups = LeadEntryGroup.objects.filter(lead__project=self.project).order_by('order')
        self.group_id_title_map = {x.id: x.title for x in lead_groups}
        # Create matrix of labels and groups

        self.group_label_matrix = {
            (group.lead_id, group.id): {
                _id: None for _id in self.label_id_title_map.keys()
            }
            for group in lead_groups
        }

        self.lead_id_titles_map = {
            _id: title
            for _id, title in Lead.objects.filter(
                project=self.project,
                id__in=[_id for _id, _ in self.group_label_matrix.keys()]
            ).values_list('id', 'title')
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

    def log_error(self, message, **kwargs):
        logger.error(f'[EXPORT:{self.export_object.id}] {message}', **kwargs)

    def load_exportable_titles(self, data, regions):
        export_type = data.get('type')
        col_type = data.get('col_type')
        exportable_titles = []

        if export_type == 'geo' and regions:
            self.region_data = {}

            for region in regions:
                admin_levels = region.adminlevel_set.all()
                admin_level_data = []

                exportable_titles.append(f'{region.title} Polygons')
                for admin_level in admin_levels:
                    exportable_titles.append(admin_level.title)
                    exportable_titles.append('{} (code)'.format(admin_level.title))

                    # Collect geo area names for each admin level
                    admin_level_data.append({
                        'id': admin_level.id,
                        'geo_area_titles': admin_level.get_geo_area_titles(),
                    })

                self.region_data[region.id] = admin_level_data

        elif export_type == 'multiple':
            index = len(exportable_titles)
            exportable_titles.extend(data.get('titles'))
            if col_type:
                for i in range(index, len(exportable_titles)):
                    self.col_types[i] = col_type[i - index]

        elif data.get('title'):
            index = len(exportable_titles)
            exportable_titles.append(data.get('title'))
            if col_type:
                self.col_types[index] = col_type
        return exportable_titles

    def load_exportables(self, exportables, regions=None):
        # Take all exportables that contains excel info
        widget_exportables = {
            exportable.widget_key: exportable
            for exportable in exportables.filter(
                data__excel__isnull=False,
            )
        }
        if self.columns is not None:
            _exportables = []
            for column in self.columns:
                if not column['is_widget']:
                    _exportables.append(column['static_column'])
                    continue
                widget_key = column['widget_key']
                exportable = widget_exportables.get(widget_key)
                if exportable:
                    _exportables.append(exportable)
                else:
                    self.log_error(f'Non-existing widget key is passed <{widget_key}>')
        else:
            _exportables = [
                *self.ColumnsData.TITLES.keys(),
                *widget_exportables.values(),
            ]
        self.exportables = _exportables

        column_titles = []

        # information_date_index = 1
        for exportable in self.exportables:
            if isinstance(exportable, str):
                titles = self.ColumnsData.TITLES.get(exportable, [])
                if callable(titles):
                    _titles = titles(self)
                else:
                    _titles = titles
                if type(_titles) not in [list, tuple]:
                    _titles = [_titles]
                column_titles.extend(_titles)
            else:
                # For each exportable, create titles according to type
                # and data
                data = exportable.data.get('excel')
                column_titles.extend(
                    self.load_exportable_titles(data, regions)
                )

        if self.decoupled and self.split:
            self.split.append([column_titles])
        self.group.append([column_titles])

        if self.decoupled and self.split:
            self.split.auto_fit_cells_in_row(1)
        self.group.auto_fit_cells_in_row(1)

        self.regions = regions
        return self

    def add_entries_from_excel_data_for_static_column(
        self,
        exportable,
        entry,
        lead,
        assignee,
    ):
        if exportable == Export.StaticColumn.LEAD_PUBLISHED_ON:
            return self.date_renderer(lead.published_on)
        if exportable == Export.StaticColumn.ENTRY_CREATED_BY:
            return entry.created_by and entry.created_by.profile.get_display_name()
        elif exportable == Export.StaticColumn.ENTRY_CREATED_AT:
            return self.date_renderer(entry.created_at)
        elif exportable == Export.StaticColumn.ENTRY_CONTROL_STATUS:
            return 'Controlled' if entry.controlled else 'Uncontrolled'
        elif exportable == Export.StaticColumn.LEAD_ID:
            return f'{lead.id}'
        elif exportable == Export.StaticColumn.LEAD_TITLE:
            return lead.title
        elif exportable == Export.StaticColumn.LEAD_URL:
            return lead.url or Permalink.lead_share_view(lead.uuid)
        elif exportable == Export.StaticColumn.LEAD_PAGE_COUNT:
            return lead.page_count  # Annotated through Prefetch on entries_qs (export.tasks_entries)
        elif exportable == Export.StaticColumn.LEAD_ORGANIZATION_TYPE_AUTHOR:
            return lead.get_authoring_organizations_type_display()
        elif exportable == Export.StaticColumn.LEAD_ORGANIZATION_AUTHOR:
            return lead.get_authors_display()
        elif exportable == Export.StaticColumn.LEAD_ORGANIZATION_SOURCE:
            return lead.get_source_display()
        elif exportable == Export.StaticColumn.LEAD_PRIORITY:
            return lead.get_priority_display()
        elif exportable == Export.StaticColumn.LEAD_ASSIGNEE:
            return assignee and assignee.profile.get_display_name()
        elif exportable == Export.StaticColumn.ENTRY_ID:
            return f'{entry.id}'
        elif exportable == Export.StaticColumn.LEAD_ENTRY_ID:
            return f'{lead.id}-{entry.id}'
        elif exportable == Export.StaticColumn.ENTRY_EXCERPT:
            entry_excerpt = self.get_entry_data(entry)
            if self.modified_excerpt_exists:
                return [entry_excerpt, entry.dropped_excerpt]
            return entry_excerpt

    def add_entries_from_excel_data(self, rows, data, export_data):
        export_type = data.get('type')

        if export_type == 'nested':
            children = data.get('children')
            for i, child in enumerate(children):
                if export_data is None or i >= len(export_data):
                    _export_data = None
                else:
                    _export_data = export_data[i]
                self.add_entries_from_excel_data(
                    rows,
                    child,
                    _export_data,
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
                    export_data_values = export_data.get('values')
                    if export_data.get('widget_key') == Widget.WidgetType.DATE_RANGE.value:
                        if len(export_data_values) == 2 and any(export_data_values):
                            rows.add_value_list([
                                self.date_renderer(deep_date_parse(export_data_values[0], raise_exception=False)),
                                self.date_renderer(deep_date_parse(export_data_values[1], raise_exception=False)),
                            ])
                    else:
                        rows.add_value_list(export_data_values)
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
        if entry.entry_type == Entry.TagType.EXCERPT:
            return entry.excerpt

        if entry.entry_type == Entry.TagType.IMAGE:
            return entry.get_image_url()

        if entry.entry_type == Entry.TagType.DATA_SERIES:
            try:
                return self.get_data_series(entry)
            except Exception:
                self.log_error(
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
                link = f'#\'{entries_sheet_name}\'!A{i + 2}'
                self.group_label_matrix[key][group_label.label_id] = get_hyperlink(link, entry.excerpt[:50])

            lead = entry.lead
            assignee = lead.get_assignee()
            rows = RowsBuilder(self.split, self.group, self.decoupled)

            for exportable in self.exportables:
                if isinstance(exportable, str):
                    # Static columns
                    values = self.add_entries_from_excel_data_for_static_column(
                        exportable,
                        entry,
                        lead,
                        assignee,
                    )
                    if type(values) in [list, tuple]:
                        rows.add_value_list(values)
                    else:
                        rows.add_value(values)
                else:
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
                self.lead_id_titles_map.get(leadid),
                self.group_id_title_map.get(gid),
                *labeldata.values(),
            ]
            self.entry_groups_sheet.append([row_data])
        return self

    def add_bibliography_sheet(self, leads_qs):
        self.bibliography_sheet.append([['Author', 'Source', 'Published Date', 'Title', 'Entries Count']])
        qs = leads_qs
        # This is annotated from LeadGQFilterSet.filter_queryset if not use total entries count
        if 'filtered_entry_count' not in qs.query.annotations:
            qs = qs.annotate(
                filtered_entry_count=models.functions.Coalesce(
                    models.Subquery(
                        Entry.objects.filter(
                            project=self.project,
                            analysis_framework=self.project.analysis_framework_id,
                            lead=models.OuterRef('pk'),
                        ).order_by().values('lead')
                        .annotate(count=models.Count('id'))
                        .values('count'),
                        output_field=models.IntegerField(),
                    ), 0,
                )
            )
        for lead in qs:
            self.bibliography_sheet.append(
                [[
                    lead.get_authors_display(),
                    lead.get_source_display(),
                    self.date_renderer(lead.published_on),
                    get_hyperlink(lead.url, lead.title) if lead.url else lead.title,
                    lead.filtered_entry_count,
                ]]
            )

    def export(self, leads_qs):
        """
        Export and return export data
        """
        self.group.set_col_types(self.col_types)
        if self.split:
            self.split.set_col_types(self.col_types)

        # Add bibliography
        self.add_bibliography_sheet(leads_qs)

        buffer = self.wb.save()
        return ContentFile(buffer)
