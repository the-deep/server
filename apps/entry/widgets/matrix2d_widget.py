WIDGET_ID = 'matrix2dWidget'
DATA_VERSION = 1


def update_attribute(widget, data, widget_data):
    data = (data or {}).get('value', {})
    dimensions = widget_data.get('dimensions', [])
    sectors = widget_data.get('sectors', [])

    filter1_values = []
    filter2_values = []

    excel_values = []
    report_values = []

    for key, dimension in data.items():
        dim_exists = False

        dimension_data = next((
            d for d in dimensions
            if d.get('id') == key
        ), {})
        subdimensions = dimension_data.get('subdimensions', [])

        for sub_key, subdimension in dimension.items():
            subdim_exists = False

            subdimension_data = next((
                s for s in subdimensions
                if s.get('id') == sub_key
            ), {})

            for sector_key, subsectors in subdimension.items():
                if subsectors is not None:
                    if isinstance(subsectors, bool):
                        subsectors = []
                    dim_exists = True
                    subdim_exists = True

                    if sector_key not in filter2_values:
                        filter2_values.append(sector_key)
                    filter2_values.extend(subsectors)

                    sector_data = next((
                        s for s in sectors
                        if s.get('id') == sector_key
                    ), {})

                    def get_ss_title(ss):
                        return next((
                            ssd.get('title') for ssd
                            in sector_data.get('subsectors', [])
                            if ssd.get('id') == ss
                        ), '')

                    excel_values.append([
                        dimension_data.get('title'),
                        subdimension_data.get('title'),
                        sector_data.get('title'),
                        [get_ss_title(ss) for ss in subsectors],
                    ])
                    report_values.append(
                        '{}-{}-{}'.format(sector_key, key, sub_key)
                    )

            if subdim_exists:
                filter1_values.append(sub_key)
        if dim_exists:
            filter1_values.append(key)

    return {
        'filter_data': [
            {
                'key': '{}-dimensions'.format(widget.key),
                'values': filter1_values,
            },
            {
                'key': '{}-sectors'.format(widget.key),
                'values': filter2_values,
            },
        ],

        'export_data': {
            'data': {
                'common': {
                    'widget_id': WIDGET_ID,
                    'widget_key': widget.key,
                    'version': DATA_VERSION,
                },
                'excel': {
                    'type': 'lists',
                    'values': excel_values,
                },
                'report': {
                    'keys': report_values,
                },
            },
        }
    }


def _get_headers(widgets_meta, widget, widget_data):
    if widgets_meta.get(widget.pk) is not None:
        widget_meta = widgets_meta[widget.pk]
        return (
            widget_meta['dimension_header_map'],
            widget_meta['subdimension_header_map'],
            widget_meta['sector_header_map'],
            widget_meta['subsector_header_map'],
        )

    dimension_header_map = {}
    subdimension_header_map = {}

    for dimension in widget_data.get('dimensions', []):
        subdimension_keys = []
        dimension_header_map[dimension['id']] = dimension
        for subdimension in dimension['subdimensions']:
            subdimension_header_map[subdimension['id']] = subdimension
            subdimension_keys.append(subdimension['id'])
        dimension_header_map[dimension['id']]['subdimension_keys'] = subdimension_keys

    sector_header_map = {}
    subsector_header_map = {}

    for sector in widget_data.get('sectors', []):
        subsector_keys = []
        sector_header_map[sector['id']] = sector
        for subsector in sector['subsectors']:
            subsector_header_map[subsector['id']] = subsector
            subsector_keys.append(subsector['id'])
        sector_header_map[sector['id']]['subsector_keys'] = subsector_keys
    widgets_meta[widget.pk] = {
        'dimension_header_map': dimension_header_map,
        'subdimension_header_map': subdimension_header_map,
        'sector_header_map': sector_header_map,
        'subsector_header_map': subsector_header_map,
    }
    return (
        dimension_header_map,
        subdimension_header_map,
        sector_header_map,
        subsector_header_map,
    )


def _get_subsectors(subsector_header_map, sector_header, subsectors):
    subsectors_header = []
    for subsector_key in subsectors:
        subsector_header = subsector_header_map.get(subsector_key)
        if subsector_header and subsector_key in sector_header['subsector_keys']:
            subsectors_header.append(
                {'id': subsector_header['id'], 'title': subsector_header['title']}
            )
    return subsectors_header


def get_comprehensive_data(widgets_meta, widget, data, widget_data):
    data = (data or {}).get('value') or {}

    values = []
    (
        dimension_header_map, subdimension_header_map,
        sector_header_map, subsector_header_map,
    ) = _get_headers(widgets_meta, widget, widget_data)

    for dimension_key, dimension_value in data.items():
        for subdimension_key, subdimension_value in dimension_value.items():
            for sector_key, selected_subsectors in subdimension_value.items():
                dimension_header = dimension_header_map.get(dimension_key)
                subdimension_header = subdimension_header_map.get(subdimension_key)
                sector_header = sector_header_map.get(sector_key)
                if (
                        dimension_header is None or
                        subdimension_header is None or
                        sector_header is None or
                        subdimension_key not in dimension_header['subdimension_keys']
                ):
                    continue
                values.append({
                    'dimension': {'id': dimension_header['id'], 'title': dimension_header['title']},
                    'subdimension': {'id': subdimension_header['id'], 'title': subdimension_header['title']},
                    'sector': {'id': sector_header['id'], 'title': sector_header['title']},
                    'subsectors': _get_subsectors(
                        subsector_header_map, sector_header, selected_subsectors,
                    ),
                })
    return values
