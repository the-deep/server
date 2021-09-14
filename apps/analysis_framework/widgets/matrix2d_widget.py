WIDGET_ID = 'matrix2dWidget'


"""
PROPERTIES:
    rows: [
        clientId: string    # TODO: Change this to key or any other name
        label: string
        tooltip?: string
        order: number
        color: string
        subRows: [
            clientId: string  # TODO: Change this to key or any other name
            label: string
            tooltip?: string
            order: number
        ]
    ]
    columns: [
        clientId: string  # TODO: Change this to key or any other name
        label: string
        tooltip?: string
        order: number
        subColumns: [
            clientId: string  # TODO: Change this to key or any other name
            label: string
            tooltip?: string
            order: number
        ]
    ]
}
"""


def get_filters(widget, properties):
    """
    Old <-> New
    dimensions <-> rows
    subdimensions <-> subRows
    sectors <-> columns
    subsectors <-> subColumns
    """
    from analysis_framework.models import Filter  # To avoid circular import

    dimension_options = []
    dimensions = properties.get('rows', [])

    for dimension in dimensions:
        dimension_options.append({
            'label': dimension.get('label'),
            'key': dimension.get('clientId'),
        })

        subdimensions = dimension.get('subRows', [])
        for subdimension in subdimensions:
            dimension_options.append({
                'label': '{} / {}'.format(
                    dimension.get('label'),
                    subdimension.get('label'),
                ),
                'key': subdimension.get('clientId'),
            })

    sector_options = []
    sectors = properties.get('columns', [])

    for sector in sectors:
        sector_options.append({
            'label': sector.get('label'),
            'key': sector.get('clientId'),
        })

        subsectors = sector.get('subColumns', [])
        for subsector in subsectors:
            sector_options.append({
                'label': '{} / {}'.format(
                    sector.get('label'),
                    subsector.get('label'),
                ),
                'key': subsector.get('clientId'),
            })

    return [{
        'title': '{} Dimensions'.format(widget.title),
        'filter_type': Filter.FilterType.LIST,
        'key': '{}-dimensions'.format(widget.key),
        'properties': {
            'type': 'multiselect',
            'options': dimension_options,
        },
    }, {
        'title': '{} Sectors'.format(widget.title),
        'filter_type': Filter.FilterType.LIST,
        'key': '{}-sectors'.format(widget.key),
        'properties': {
            'type': 'multiselect',
            'options': sector_options,
        },
    }]


def get_exportable(widget, properties):
    excel = {
        'type': 'multiple',
        'titles': [
            '{} - Dimension'.format(widget.title),
            '{} - Subdimension'.format(widget.title),
            '{} - Sector'.format(widget.title),
            '{} - Subsectors'.format(widget.title),
        ],
    }

    report = {
        'levels': [
            {
                'id': sector.get('clientId'),
                'title': sector.get('label'),
                'sublevels': [
                    {
                        'id': '{}-{}'.format(
                            sector.get('clientId'),
                            dimension.get('clientId'),
                        ),
                        'title': dimension.get('label'),
                        'sublevels': [
                            {
                                'id': '{}-{}-{}'.format(
                                    sector.get('clientId'),
                                    dimension.get('clientId'),
                                    subdimension.get('clientId'),
                                ),
                                'title': subdimension.get('label'),
                            } for subdimension
                            in dimension.get('subRows', [])
                        ]
                    } for dimension in properties.get('rows', [])
                ],
            } for sector in properties.get('columns', [])
        ],
    }

    return {
        'excel': excel,
        'report': report,
    }
