def get_filters(widget, data):
    dimension_options = []
    dimensions = data.get('dimensions', [])

    for dimension in dimensions:
        dimension_options.append({
            'label': dimension.get('title'),
            'key': dimension.get('id'),
        })

        subdimensions = dimension.get('subdimensions', [])
        for subdimension in subdimensions:
            dimension_options.append({
                'label': '{} / {}'.format(
                    dimension.get('title'),
                    subdimension.get('title'),
                ),
                'key': subdimension.get('id'),
            })

    sector_options = []
    sectors = data.get('sectors', [])

    for sector in sectors:
        sector_options.append({
            'label': sector.get('title'),
            'key': sector.get('id'),
        })

        subsectors = sector.get('subsectors', [])
        for subsector in subsectors:
            sector_options.append({
                'label': '{} / {}'.format(
                    sector.get('title'),
                    subsector.get('title'),
                ),
                'key': subsector.get('id'),
            })

    return [{
        'title': '{} Dimensions'.format(widget.title),
        'filter_type': 'list',
        'key': '{}-dimensions'.format(widget.key),
        'properties': {
            'type': 'multiselect',
            'options': dimension_options,
        },
    }, {
        'title': '{} Sectors'.format(widget.title),
        'filter_type': 'list',
        'key': '{}-sectors'.format(widget.key),
        'properties': {
            'type': 'multiselect',
            'options': sector_options,
        },
    }]


def get_exportable(widget, data):
    excel = {
        'type': 'multiple',
        'titles': ['Dimension', 'Subdimension', 'Sector', 'Subsectors'],
    }

    report = {
        'levels': [
            {
                'id': sector.get('id'),
                'title': sector.get('title'),
                'sublevels': [
                    {
                        'id': '{}-{}'.format(
                            sector.get('id'),
                            dimension.get('id'),
                        ),
                        'title': dimension.get('title'),
                        'sublevels': [
                            {
                                'id': '{}-{}-{}'.format(
                                    sector.get('id'),
                                    dimension.get('id'),
                                    subdimension.get('id'),
                                ),
                                'title': subdimension.get('title'),
                            } for subdimension
                            in dimension.get('subdimensions', [])
                        ]
                    } for dimension in data.get('dimensions', [])
                ],
            } for sector in data.get('sectors', [])
        ],
    }

    return {
        'excel': excel,
        'report': report,
    }
