from openpyxl import load_workbook


def extract_meta(xlsx_file):
    workbook = load_workbook(xlsx_file, data_only=True, read_only=True)
    wb_sheets = []
    for index, wb_sheet in enumerate(workbook.worksheets):
        if wb_sheet.sheet_state != 'hidden':
            wb_sheets.append({
                'key': str(index),
                'title': wb_sheet.title,
            })
    return {
        'sheets': wb_sheets,
    }
