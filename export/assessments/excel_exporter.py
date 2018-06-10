from collections import OrderedDict

from django.core.files.base import ContentFile

from export.models import Export
from export.formats.xlsx import WorkBook, RowsBuilder
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

        # Initial titles
        self.titles = [
            'Date of Lead Publication',
            'Imported By',
            'Lead Title',
            'Source',
        ]
        self._titles_dict = {k: True for k in self.titles}

    def to_flattened_key_vals(self, dictdata):
        """
        Convert nested dictionary data to flat dict with keys and nondict values
        """
        flat = OrderedDict()  # to preserve order of titles
        for k, v in dictdata.items():
            if isinstance(v, dict):
                # NOTE: this might override the keys in recursive calls
                flat.update(self.to_flattened_key_vals(v))
            elif isinstance(v, list):
                # check if lise elements are dict or not
                for i in v:
                    if isinstance(i, dict):
                        flat.update(self.to_flattened_key_vals(i))
                    else:
                        flat[k] = flat.get(k, []) + [i]
            else:
                # Just add key value
                flat[k] = v
        return flat

    def add_assessments(self, assessments):
        for a in assessments:
            self.add_assessment(a)
        return self

    def add_assessment(self, assessment):
        jsondata = assessment.to_exportable_json()
        flat = self.to_flattened_key_vals(jsondata)
        logger.info(flat)
        rows = RowsBuilder(self.split, self.group, split=False)
        rows.add_value_list([
            format_date(assessment.lead.created_at),
            assessment.lead.created_by.username,
            assessment.lead.title,
            assessment.lead.source
        ])
        # update the titles
        for k, v in flat.items():
            if not self._titles_dict.get(k):
                self.titles.append(k)
                self._titles_dict[k] = True

        for t in self.titles:
            v = flat.get(t)
            if v:
                val = ', '.join(v) if isinstance(v, list) else str(v)
                rows.add_value(val)

        self.group.append([self.titles])

        if self.decoupled and self.split:
            self.split.auto_fit_cells_in_row(1)
        self.group.auto_fit_cells_in_row(1)

        rows.apply()
        return self
        # Get keys
        # Add metadata keys
        """
        metadata = jsondata['metadata']
        metadata_keys = []
        for k, v in metadata.items():
            for item in v:
                metadata_keys.extend(list(item.keys()))
        self.titles.extend(metadata_keys)
        methodology = jsondata['methodology']
        methodology_keys = ['Affected Groups']
        for attr in methodology['Attributes']:
            for k, v in attr.items():
                for e in v:
                    methodology_keys.extend(list(e.keys()))
        methodology_keys.extend([
            'Data Collection Techniques',
            'Focuses',
            'Limitations',
            'Objectives',
            'Sampling',
            'Sectors'
        ])
        self.titles.extend(methodology_keys)
        logger.info(self.titles)
        self.group.append([self.titles])

        if self.decoupled and self.split:
            self.split.auto_fit_cells_in_row(1)
        self.group.auto_fit_cells_in_row(1)

        rows = RowsBuilder(self.split, self.group, split=False)
        rows.add_value_list([
            format_date(assessment.lead.created_at),
            assessment.lead.created_by.username,
            assessment.lead.title,
            assessment.lead.source
        ])
        # now add metadata
        for k, v in metadata.items():
            for x in v:
                rows.add_value_list([
                    ', '.join(v) if type(v) == list else str(v)
                    for _, v in x.items()
                ])
        # add methodology
        rows.add_value(', '.join(methodology['Affected Groups']))
        # add methodology attributes
        for attr in methodology['Attributes']:
            for k, v in attr.items():
                # rows.add_value.extend(list(v.keys()))
                for x in v:
                    rows.add_value_list([
                        ', '.join(val) if type(val) == list else str(val)
                        for _, val in x.items()
                    ])
        # add remaining methodology items
        for k, v in methodology.items():
            if k != 'Affected Groups' and k != 'Attributes':
                rows.add_value(','.join(v) if type(v) == list else str(v))
        # TODO: summary and score tabs
        rows.apply()
        logger.info(rows.group_rows)
        return self
        """

    def export(self, export_entity):
        buffer = self.wb.save()
        filename = generate_filename('Assessments Export', 'xlsx')

        export_entity.title = filename
        export_entity.type = Export.ASSESSMENTS
        export_entity.format = 'xlsx'
        export_entity.pending = False
        export_entity.mime_type = EXCEL_MIME_TYPE

        export_entity.file.save(filename, ContentFile(buffer))
        export_entity.save()
