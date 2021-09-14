from analysis_framework.widgets.matrix1d_widget import WIDGET_ID

DATA_VERSION = 1


def update_attribute(widget, data, widget_properties):
    filter_values = []
    excel_values = []
    report_values = []

    data = (data or {}).get('value', {})
    rows = widget_properties.get('rows', [])

    for row_key, row in data.items():
        row_exists = False
        row_data = next((
            r for r in rows
            if r.get('cliendId') == row_key
        ), {})
        cells = row_data.get('cells', [])

        if not row:
            continue

        for cell_key, cell in row.items():
            if cell:
                row_exists = True
                cell_data = next((
                    c for c in cells
                    if c.get('cliendId') == cell_key
                ), {})

                filter_values.append(cell_key)

                excel_values.append([
                    row_data.get('label'),
                    cell_data.get('label'),
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
            }
        },

    }


def _get_headers(widgets_meta, widget, widget_properties):
    if widgets_meta.get(widget.pk) is not None:
        widget_meta = widgets_meta[widget.pk]
        return (
            widget_meta['pillar_header_map'],
            widget_meta['subpillar_header_map'],
        )

    pillar_header_map = {}
    subpillar_header_map = {}

    for pillar in widget_properties.get('rows', []):
        subpillar_keys = []
        pillar_header_map[pillar['clientId']] = pillar
        for subpillar in pillar['cells']:
            subpillar_header_map[subpillar['clientId']] = subpillar
            subpillar_keys.append(subpillar['clientId'])
        pillar_header_map[pillar['clientId']]['subpillar_keys'] = subpillar_keys
    widgets_meta[widget.pk] = {
        'pillar_header_map': pillar_header_map,
        'subpillar_header_map': subpillar_header_map,
    }
    return pillar_header_map, subpillar_header_map


def get_comprehensive_data(widgets_meta, widget, _data, widget_properties):
    data = (_data or {}).get('value') or {}

    pillar_header_map, subpillar_header_map = _get_headers(
        widgets_meta, widget, widget_properties,
    )

    values = []

    for pillar_key, pillar_value in data.items():
        for subpillar_key, subpillar_selected in pillar_value.items():
            pillar_header = pillar_header_map.get(pillar_key)
            subpillar_header = subpillar_header_map.get(subpillar_key)
            if (
                    not subpillar_selected or
                    pillar_header is None or
                    subpillar_header is None or
                    subpillar_key not in pillar_header.get('subpillar_keys', [])
            ):
                continue
            values.append({
                'id': subpillar_header['clientId'],
                'value': subpillar_header['label'],
                'row': {'id': pillar_header['clientId'], 'title': pillar_header['label']},
            })
    return values
