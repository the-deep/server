def update_attribute(widget, data, widget_data):
    filter_values = []
    excel_values = []
    report_values = []

    data = (data or {}).get('value', {})
    rows = widget_data.get('rows', [])

    for row_key, row in data.items():
        row_exists = False
        row_data = next((
            r for r in rows
            if r.get('key') == row_key
        ), {})
        cells = row_data.get('cells', [])

        for cell_key, cell in row.items():
            if cell:
                row_exists = True
                cell_data = next((
                    c for c in cells
                    if c.get('key') == cell_key
                ), {})

                filter_values.append(cell_key)

                excel_values.append([
                    row_data.get('title'),
                    cell_data.get('value'),
                ])
                report_values.append('{}-{}'.format(row_key, cell_key))

        if row_exists:
            filter_values.append(row_key)

    return {
        'filter_data': [{
            'values': filter_values,
        }],

        'export_data': {
            'data': {
                'excel': {
                    'type': 'lists',
                    'values': excel_values,
                },
                'report': {
                    'keys': report_values,
                },
            }
        },

    }
