from collections import OrderedDict

from django.core.files.base import ContentFile

from export.models import Export
from export.formats.xlsx import WorkBook, RowsBuilder
from openpyxl.styles import Alignment
from export.mime_types import EXCEL_MIME_TYPE
from utils.common import format_date, generate_filename

import logging

logger = logging.getLogger('django')


class ExcelExporter:
    def __init__(self, decoupled=True):
        self.wb = WorkBook()

        # Create two worksheets
        if decoupled:
            self.split = self.wb.get_active_sheet()\
                .set_title('Split Assessments')
            self.group = self.wb.create_sheet('Grouped Assessments')
        else:
            self.split = None
            self.group = self.wb.get_active_sheet().set_title('Assessments')
        self.decoupled = decoupled

        # Cells to be merged
        self.merge_cells = {}
        # Initial titles
        self.lead_titles = [
            'Date of Lead Publication',
            'Imported By',
            'Lead Title',
            'Source',
        ]
        self.titles = [*self.lead_titles]
        self.col_types = {
            0: 'date',
        }
        self._titles_dict = {k: True for k in self.titles}

        self._headers_titles = OrderedDict()
        self._headers_added = False
        self._excel_rows = []
        self._title_headers = []
        self._headers_dict = {}
        self._flats = []
        self._assessments = []

    def to_flattened_key_vals(self, dictdata, parents=[]):
        """
        Convert nested dictionary data to flat dict with keys and nondict
        values.
        @dictdata: nested dict structrure to be flattened
        @parents: parent titles for given level of title.
                Order [immediate parent, next parent, ... root]
        """
        flat = OrderedDict()  # to preserve order of titles
        for k, v in dictdata.items():
            if isinstance(v, dict):
                # NOTE: this might override the keys in recursive calls
                flat.update(self.to_flattened_key_vals(v, [k, *parents]))
            elif isinstance(v, list):
                # check if list elements are dict or not
                for i in v:
                    if isinstance(i, dict):
                        flat.update(
                            self.to_flattened_key_vals(i, [k, *parents])
                        )
                    else:
                        vals = flat.get(k, {}).get('value', [])
                        vals.append(i)
                        # FIXME: assigning parents is repeated every step
                        flat[k] = {'value': vals, 'parents': parents}
            else:
                # Just add key value
                flat[k] = {'value': v, 'parents': parents}
        return flat

    def add_assessments(self, assessments):
        for a in assessments:
            self.add_assessment(a)
        return self

    def add_assessment(self, assessment):
        jsondata = assessment.to_exportable_json()
        flat = self.to_flattened_key_vals(jsondata)
        self._flats.append(flat)
        self._assessments.append(assessment)

        # update the titles
        for k, v in flat.items():
            parent = v['parents'][-1]
            header_titles = self._headers_titles.get(parent, [])

            if k not in header_titles:
                header_titles.append(k)
            self._headers_titles[parent] = header_titles
            '''
            if not self._titles_dict.get(k):
                self.titles.append(k)
                self._titles_dict[k] = True
            '''
        return self

    def get_titles(self):
        return [
            *self.lead_titles,
            *[y for k, v in self._headers_titles.items() for y in v]
        ]

    def assessments_to_rows(self):
        for index, assessment in enumerate(self._assessments):
            rows = RowsBuilder(self.split, self.group, split=False)
            rows.add_value_list([
                format_date(assessment.lead.created_at),
                assessment.lead.created_by.username,
                assessment.lead.title,
                assessment.lead.source
            ])
            headers_dict = {}
            flat = self._flats[index]
            for i, t in enumerate(self.get_titles()):
                v = flat.get(t)
                if not v and t not in self.lead_titles:
                    rows.add_value("")
                    self._title_headers.append("")
                    continue
                elif not v:
                    self._title_headers.append("")
                    continue

                v = flat[t]['value']
                val = ', '.join([str(x) for x in v]) if isinstance(v, list) else str(v)
                rows.add_value(val)
                header = flat[t]['parents'][-1]

                if not self._headers_dict.get(header):
                    self._title_headers.append(header.upper())
                    self._headers_dict[header] = True
                else:
                    self.merge_cells[header]['end'] += 1

                if not headers_dict.get(header):
                    self.merge_cells[header] = {'start': i, 'end': i}
                    headers_dict[header] = True
                else:
                    self._title_headers.append("")

            self._excel_rows.append(rows)

    def export(self):
        # Generate rows
        self.assessments_to_rows()

        # add header rows
        headerrows = RowsBuilder(self.split, self.group, split=False)
        headerrows.add_value_list(self._title_headers)
        headerrows.apply()

        self.group.append([self.get_titles()])

        if self.decoupled and self.split:
            self.split.auto_fit_cells_in_row(1)
        self.group.auto_fit_cells_in_row(1)

        # add rows
        for rows in self._excel_rows:
            rows.apply()

        # merge cells
        if self.merge_cells:
            sheet = self.wb.wb.active
            for k, v in self.merge_cells.items():
                sheet.merge_cells(
                    start_row=1, start_column=v['start'] + 1,
                    end_row=1, end_column=v['end'] + 1
                )
                cell = sheet.cell(row=1, column=v['start'] + 1)
                cell.alignment = Alignment(horizontal='center')

        self.group.set_col_types(self.col_types)
        if self.split:
            self.split.set_col_types(self.col_types)

        buffer = self.wb.save()
        filename = generate_filename('Assessments Export', 'xlsx')
        return filename, Export.XLSX, EXCEL_MIME_TYPE, ContentFile(buffer)
