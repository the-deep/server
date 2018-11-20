from openpyxl import load_workbook
from utils.common import random_key

from ..models import Sheet, Field


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


def extract_meta(book):
    with book.get_file() as xlsx_file:
        workbook = load_workbook(xlsx_file, data_only=True, read_only=True)
        wb_sheets = []
        for index, wb_sheet in enumerate(workbook.worksheets):
            wb_sheets.append({
                'key': str(index),
                'title': wb_sheet.title,
            })
        book.meta = {
            'sheets': wb_sheets,
        }


def extract(book):
    options = book.options if book.options else {}
    Sheet.objects.filter(book=book).delete()  # Delete all previous sheets
    with book.get_file() as xlsx_file:
        workbook = load_workbook(xlsx_file, data_only=True, read_only=True)
        for sheet_key, wb_sheet in enumerate(workbook.worksheets):
            sheet_options = options['sheets'].get(str(sheet_key), {})
            if sheet_options.get('skip', True):
                continue
            sheet = Sheet.objects.create(
                title=wb_sheet.title,
                book=book,
            )
            header_index = sheet_options['header_row']
            data_index = sheet_options.get('data_row_index', header_index + 1)

            # Fields
            header_row = list(
                wb_sheet.iter_rows(
                    min_row=header_index, max_row=header_index + 1,
                )
            )[0]
            fields = []
            columns = []
            ordering = 1
            for cell in header_row:
                if cell.value is not None:
                    columns.append(cell.column)
                    fields.append(
                        Field(
                            title=cell.value,
                            sheet=sheet,
                            ordering=ordering,
                        )
                    )
                else:
                    fields.append(None)
                ordering += 1
            Field.objects.bulk_create(
                [field for field in fields if field is not None]
            )

            # Data
            rows = []
            for _row in wb_sheet.iter_rows(row_offset=data_index):
                row = {}
                if is_row_empty(_row, columns):
                    continue
                try:
                    for index, field in enumerate(fields):
                        if field is None:
                            continue
                        row[str(field.pk)] = _row[index].value
                    row['key'] = random_key()
                    rows.append(row)
                except Exception:
                    pass
            sheet.data = rows
            sheet.save()
