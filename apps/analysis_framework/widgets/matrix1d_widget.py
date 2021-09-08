WIDGET_ID = 'matrix1dWidget'


def get_filters(widget, data):
    rows = data.get('rows', [])
    filter_options = []
    for row in rows:
        filter_options.append({
            'label': row.get('title'),
            'key': row.get('key'),
        })
        cells = row.get('cells', [])

        for cell in cells:
            filter_options.append({
                'label': '{} / {}'.format(
                    row.get('title'),
                    cell.get('value'),
                ),
                'key': cell.get('key'),
            })

    return [{
        'filter_type': 'list',
        'properties': {
            'type': 'multiselect',
            'options': filter_options,
        },
    }]


def get_exportable(widget, data):
    rows = data.get('rows', [])
    excel = {
        'type': 'multiple',
        'titles': [
            '{} - Dimension'.format(widget.title),
            '{} - Subdimension'.format(widget.title),
        ],
    }

    report = {
        'levels': [
            {
                'id': row.get('key'),
                'title': row.get('title'),
                'sublevels': [
                    {
                        'id': '{}-{}'.format(row.get('key'), cell.get('key')),
                        'title': cell.get('value'),
                    } for cell in row.get('cells', [])
                ],
            } for row in rows
        ],
    }

    return {
        'excel': excel,
        'report': report,
    }
