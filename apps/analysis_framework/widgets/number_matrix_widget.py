WIDGET_ID = 'numberMatrixWidget'


def get_filters(widget, data):
    return [{
        'filter_type': 'number',
        'properties': {
            'type': 'number-2d',
        },
    }]


def get_exportable(widget, data):
    titles = []

    row_headers = data.get('row_headers', [])
    for row_header in row_headers:
        column_headers = data.get('column_headers', [])
        for column_header in column_headers:
            titles.append('{} - {}'.format(
                row_header.get('title'),
                column_header.get('title'),
            ))

        titles.append('{} - Matches'.format(row_header.get('title')))

    return {
        'excel': {
            'type': 'multiple',
            'titles': titles,
            # TODO: col_type to list full of 'number'
        },
    }
