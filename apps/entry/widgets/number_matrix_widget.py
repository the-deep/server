WIDGET_ID = 'numberMatrixWidget'
DATA_VERSION = 1


def update_attribute(widget, _data, widget_data):
    data = (_data or {}).get('value') or {}
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
                'common': {
                    'widget_id': WIDGET_ID,
                    'widget_key': widget.key,
                    'version': DATA_VERSION,
                },
                'excel': {
                    'values': excel_values,
                },
            }
        }
    }


def get_comprehensive_data(widgets_meta, widget, _data, widget_data):
    data = (_data or {}).get('value') or {}

    if widgets_meta.get(widget.pk) is None:
        row_headers_map = {
            row['key']: row
            for row in widget_data.get('row_headers', [])
        }
        column_headers_map = {
            col['key']: col
            for col in widget_data.get('column_headers', [])
        }
        widgets_meta[widget.pk] = {
            'row_headers_map': row_headers_map,
            'column_headers_map': column_headers_map,
        }
    else:
        widget_meta = widgets_meta[widget.pk]
        row_headers_map = widget_meta['row_headers_map']
        column_headers_map = widget_meta['column_headers_map']

    values = []
    for row_key, row_value in data.items():
        for col_key, value in row_value.items():
            row_header = row_headers_map.get(row_key)
            col_header = column_headers_map.get(col_key)
            if row_header and col_header:
                values.append({
                    'value': value,
                    'row': {'id': row_key, 'title': row_header['title']},
                    'column': {'id': col_key, 'title': col_header['title']},
                })
    return values
