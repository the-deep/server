import logging
from openpyxl import load_workbook

from ..models import Sheet, Field
from datetime import datetime

from utils.common import (
    LogTime,
    excel_to_python_date_format,
    format_date_or_iso,
)

logger = logging.getLogger(__name__)


def get_cell_value(row, column):
    try:
        return row[column].value
    except IndexError:
        return None


def is_row_empty(row, columns):
    for column in columns:
        if column is not None:
            value = get_cell_value(row, column)
            if value is not None:
                return False
    return True


def get_excel_value(cell):
    value = cell.value
    if value is not None and isinstance(value, datetime):
        dateformat = cell.number_format
        # try casting to python format
        python_format = excel_to_python_date_format(
            dateformat
        )
        return format_date_or_iso(
            cell.value, python_format
        )
    elif value is not None and not isinstance(value, str):
        return cell.internal_value
    return value


@LogTime()
def extract(book):
    options = book.options if book.options else {}
    Sheet.objects.filter(book=book).delete()  # Delete all previous sheets
    with book.get_file() as xlsx_file:
        workbook = load_workbook(xlsx_file, data_only=True, read_only=True)
        for sheet_key, wb_sheet in enumerate(workbook.worksheets):
            sheet_options = options.get('sheets', {}).get(str(sheet_key), {})
            if sheet_options.get('skip', False):
                continue
            sheet = Sheet.objects.create(
                title=wb_sheet.title,
                book=book,
            )
            header_index = sheet_options.get('header_row', 1)
            no_headers = sheet_options.get('no_headers', False)
            data_index = header_index

            if no_headers:
                data_index -= 1

            # Fields
            header = wb_sheet.iter_rows(
                min_row=header_index, max_row=header_index + 1
            )
            header_row = next(header, None)
            if header_row is None:
                # No point in creating sheet when there is no header
                logger.warning("Can't get header for"
                               "Sheet({}) {}".format(sheet.id, sheet.title))
                return

            fields = []
            columns = []
            ordering = 1
            for cell in header_row:
                if cell.value is not None:
                    columns.append(cell.column)
                    fields.append(
                        Field(
                            title=(cell.value if not no_headers
                                   else 'Column ' + str(ordering)),
                            sheet=sheet,
                            ordering=ordering,
                            data=[{
                                'value': cell.value,
                                'empty': False,
                                'invalid': False
                            }]
                        )
                    )
                else:
                    fields.append(None)
                ordering += 1

            Field.objects.bulk_create(
                [field for field in fields if field is not None]
            )

            fields_data = {}
            # Data
            for _row in wb_sheet.iter_rows(min_row=data_index + 1):
                if is_row_empty(_row, columns):
                    continue
                print(_row)
                try:
                    for index, field in enumerate(fields):
                        if field is None:
                            continue
                        value = get_excel_value(_row[index])

                        field_data = fields_data.get(field.id, [])
                        field_data.append({
                            'value': value,
                            'empty': False,
                            'invalid': False
                        })
                        fields_data[field.id] = field_data
                except Exception:
                    pass

            # Save field
            for field in sheet.field_set.all():
                field.data.extend(fields_data.get(field.id, []))
                block_name = 'Field Save xlsx extract {}'.format(field.title)
                with LogTime(block_name=block_name):
                    field.save()

            sheet.data_row_index = data_index
            sheet.save()
