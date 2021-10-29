from analysis_framework.widgets.scale_widget import WIDGET_ID


# NOTE: Please update the data version when you update the data format
DATA_VERSION = 1


def _get_scale(widget, data, widget_properties):
    selected_scale = data.get('value')
    selected_scales = [selected_scale] if selected_scale is not None else []

    options = widget_properties.get('options', [])
    scale = next((
        s for s in options
        if s['key'] == selected_scale
    ), None)
    scale = scale or {}
    return {
        # Note: Please change the DATA_VERSION when you change the data format

        # widget_id will be used to alter rendering in report
        'widget_id': getattr(widget, 'widget_id', ''),
        # widget related attributes
        'title': getattr(widget, 'title', ''),
        'label': scale.get('label'),
        'color': scale.get('color'),
    }, selected_scales


def update_attribute(widget, data, widget_properties):
    scale, selected_scales = _get_scale(widget, data, widget_properties)

    return {
        # Note: Please change the DATA_VERSION when you change the data format
        'filter_data': [{
            'values': selected_scales,
        }],

        'export_data': {
            'data': {
                'common': {
                    'widget_id': WIDGET_ID,
                    'widget_key': widget.key,
                    'version': DATA_VERSION,
                },
                'excel': {
                    'value': scale['label'],
                },
                'report': {
                    'title': scale['title'],
                    'label': scale['label'],
                    'color': scale['color'],
                }
            },
        },
    }


def get_comprehensive_data(widgets_meta, widget, data, widget_properties):
    scale, selected_scales = _get_scale(widget, data, widget_properties)
    options = widget_properties.get('options', [])

    if widgets_meta.get(widget.pk) is None:  # To avoid calculating meta at each attribute
        widgets_meta[widget.pk] = {}
        min_option, max_option = {}, {}
        if options:
            min_option, max_option = {**options[0]}, {**options[len(options) - 1]}
            min_option['key'], max_option['key'] = min_option.pop('key'), max_option.pop('key')
        widgets_meta[widget.pk] = {
            'min': min_option,
            'max': max_option,
        }

    return {
        **widgets_meta[widget.pk],
        'scale': scale,
        'label': scale['label'],
        'index': ([
            (i + 1) for i, v in enumerate(options)
            if v['key'] == selected_scales[0]
        ] or [None])[0] if selected_scales else None,
    }
