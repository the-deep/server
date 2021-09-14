WIDGET_ID = 'numberMatrixWidget'


# NOTE: THIS IS REMOVED FROM NEW UI

def get_filters(widget, properties):
    from analysis_framework.models import Filter  # To avoid circular import

    return [{
        'filter_type': Filter.FilterType.NUMBER,
        'properties': {
            'type': 'number-2d',
        },
    }]


def get_exportable(widget, properties):
    titles = []

    row_headers = properties.get('row_headers', [])
    for row_header in row_headers:
        column_headers = properties.get('column_headers', [])
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
