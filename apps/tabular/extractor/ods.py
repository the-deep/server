import logging
from datetime import datetime

import pyexcel_ods

from utils.common import LogTime

from ..models import Field, Sheet

logger = logging.getLogger(__name__)

date_type = type(datetime.now().date())


@LogTime()
def extract(book):
    options = book.options if book.options else {}
    Sheet.objects.filter(book=book).delete()  # Delete all previous sheets
    with book.get_file() as ods_file:
        workbook = pyexcel_ods.get_data(ods_file)
        for sheet_key in workbook:
            wb_sheet = workbook[sheet_key]
            sheet_options = options.get("sheets", {}).get(str(sheet_key), {})
            if sheet_options.get("skip", False):
                continue
            sheet = Sheet.objects.create(
                title=sheet_key,
                book=book,
            )
            header_index = sheet_options.get("header_row", 1) - 1
            no_headers = sheet_options.get("no_headers", False)
            data_index = header_index + 1

            if no_headers:
                data_index -= 1

            # Fields
            header_row = wb_sheet[header_index]
            fields = []
            ordering = 1

            for value in header_row:
                fields.append(
                    Field(
                        title=(value if not no_headers else "Column " + str(ordering)),
                        sheet=sheet,
                        ordering=ordering,
                        data=[{"value": value, "empty": False, "invalid": False}],
                    )
                )
                ordering += 1
            Field.objects.bulk_create(fields)

            fields_data = {}
            # Data
            for _row in wb_sheet[data_index:]:
                try:
                    for index, field in enumerate(fields):
                        field_data = fields_data.get(field.id, [])
                        value = _row[index]
                        if isinstance(value, (datetime, date_type)):
                            value = _row[index].isoformat()
                        field_data.append({"value": value, "empty": False, "invalid": False})
                        fields_data[field.id] = field_data
                except Exception:
                    pass

            # Save field
            for field in sheet.field_set.all():
                field.data.extend(fields_data.get(field.id, []))
                block_name = "Field Save ods extract {}".format(field.title)
                with LogTime(block_name=block_name):
                    field.save()

            sheet.data_row_index = data_index
            sheet.save()
