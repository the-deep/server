def update_attribute(widget, data, widget_data):
    data = data or {}
    row_headers = widget_data.get('row_headers', [])
    column_headers = widget_data.get('column_headers', [])

    excel_values = []

    for row_header in row_headers:
        row_values = []
        for column_header in column_headers:
            value = (data.get(row_header.get('key')) or {}).get(
                column_header.get('key'),
            )
            if value is None:
                excel_values.append('')
            else:
                row_values.append(value)
                excel_values.append(str(value))
        is_same = len(row_values) == 0 or len(set(row_values)) == 1
        excel_values.append('True' if is_same else 'False')

    return {
        'filter_data': [],
        'export_data': {
            'data': {
                'excel': {
                    'values': excel_values,
                },
            }
        }
    }
