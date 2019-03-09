import pyexcel_ods


def extract_meta(xlsx_file):
    workbook = pyexcel_ods.get_data(xlsx_file)
    wb_sheets = []
    for index, wb_sheet in enumerate(workbook):
        wb_sheets.append({
            'key': str(index),
            'title': wb_sheet,
        })
    return {
        'sheets': wb_sheets,
    }
