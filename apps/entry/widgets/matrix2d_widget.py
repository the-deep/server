from analysis_framework.widgets.matrix2d_widget import WIDGET_ID

DATA_VERSION = 2


def update_attribute(widget, data, widget_properties):
    data = (data or {}).get('value', {})
    rows = widget_properties.get('rows', [])
    columns = widget_properties.get('columns', [])

    filter1_values = []
    filter2_values = []

    excel_values = []
    report_values = []

    for key, row in data.items():
        dim_exists = False

        row_data = next((
            d for d in rows
            if d.get('clientId') == key
        ), {})
        sub_rows = row_data.get('subRows', [])

        if row is None:
            continue

        for sub_key, sub_row in row.items():
            subdim_exists = False

            sub_row_data = next((
                s for s in sub_rows
                if s.get('clientId') == sub_key
            ), {})

            if row is None:
                continue

            for column_key, sub_columns in sub_row.items():
                if sub_columns is not None:
                    if isinstance(sub_columns, bool):
                        sub_columns = []

                    dim_exists = True
                    subdim_exists = True

                    if column_key not in filter2_values:
                        filter2_values.append(column_key)
                    filter2_values.extend(sub_columns)

                    column_data = next((
                        s for s in columns
                        if s.get('clientId') == column_key
                    ), {})

                    def get_ss_title(ss):
                        return next((
                            ssd.get('label') for ssd
                            in column_data.get('subColumns', [])
                            if ssd.get('clientId') == ss
                        ), '')

                    excel_values.append([
                        row.get('label'),
                        sub_row_data.get('label'),
                        column_data.get('label'),
                        [get_ss_title(ss) for ss in sub_columns],
                    ])

                    # Without sub_columns {column}-{row}-{sub-row}
                    report_values.append(
                        '{}-{}-{}'.format(column_key, key, sub_key)
                    )
                    # With sub_columns {column}-{sub-column}-{row}-{sub-row}
                    report_values.extend(
                        [
                            '{}-{}-{}-{}'.format(column_key, ss, key, sub_key)
                            for ss in sub_columns
                        ]
                    )

            if subdim_exists:
                filter1_values.append(sub_key)
        if dim_exists:
            filter1_values.append(key)

    return {
        'filter_data': [
            {
                'key': '{}-rows'.format(widget.key),
                'values': filter1_values,
            },
            {
                'key': '{}-columns'.format(widget.key),
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


def _get_headers(widgets_meta, widget, widget_properties):
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

    for dimension in widget_properties.get('rows', []):
        subdimension_keys = []
        dimension_header_map[dimension['clientId']] = dimension
        for subdimension in dimension['subRows']:
            subdimension_header_map[subdimension['clientId']] = subdimension
            subdimension_keys.append(subdimension['clientId'])
        dimension_header_map[dimension['clientId']]['subdimension_keys'] = subdimension_keys

    sector_header_map = {}
    subsector_header_map = {}

    for sector in widget_properties.get('columns', []):
        subsector_keys = []
        sector_header_map[sector['clientId']] = sector
        for subsector in sector['subColumns']:
            subsector_header_map[subsector['clientId']] = subsector
            subsector_keys.append(subsector['clientId'])
        sector_header_map[sector['clientId']]['subsector_keys'] = subsector_keys
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
                {'id': subsector_header['clientId'], 'title': subsector_header['label']}
            )
    return subsectors_header


def get_comprehensive_data(widgets_meta, widget, data, widget_properties):
    data = (data or {}).get('value') or {}

    values = []
    (
        dimension_header_map, subdimension_header_map,
        sector_header_map, subsector_header_map,
    ) = _get_headers(widgets_meta, widget, widget_properties)

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
                    'dimension': {'id': dimension_header['clientId'], 'title': dimension_header['label']},
                    'subdimension': {'id': subdimension_header['clientId'], 'title': subdimension_header['label']},
                    'sector': {'id': sector_header['clientId'], 'title': sector_header['label']},
                    'subsectors': _get_subsectors(
                        subsector_header_map, sector_header, selected_subsectors,
                    ),
                })
    return values
