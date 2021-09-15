WIDGET_ID = 'matrix1dWidget'


"""
PROPERTIES:
    rows: [
        clientId: string  # TODO: Change this to key or any other name
        label: string
        tooltip?: string
        order: number
        color: string
        cells: [
            clientId: string  # TODO: Change this to key or any other name
            label: string
            tooltip?: string
            order: number
        ]
    ]
}
"""


def get_filters(widget, properties):
    from analysis_framework.models import Filter  # To avoid circular import

    rows = properties.get('rows', [])
    filter_options = []
    for row in rows:
        filter_options.append({
            'label': row.get('label'),
            'key': row.get('clientId'),
        })
        cells = row.get('cells', [])

        for cell in cells:
            filter_options.append({
                'label': '{} / {}'.format(
                    row.get('label'),
                    cell.get('label'),
                ),
                'key': cell.get('clientId'),
            })

    return [{
        'filter_type': Filter.FilterType.LIST,
        'properties': {
            'type': 'multiselect',
            'options': filter_options,
        },
    }]


def get_exportable(widget, properties):
    rows = properties.get('rows', [])
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
                'id': row.get('clientId'),
                'title': row.get('label'),
                'sublevels': [
                    {
                        'id': '{}-{}'.format(row.get('clientId'), cell.get('clientId')),
                        'title': cell.get('label'),
                    } for cell in row.get('cells', [])
                ],
            } for row in rows
        ],
    }

    return {
        'excel': excel,
        'report': report,
    }
