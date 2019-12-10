def _get_text(widget, data, widget_data):
    return str(
        data.get('value') or ''
    )


def update_attribute(*args, **kwargs):
    text = _get_text(*args, **kwargs)

    return {
        'filter_data': [{
            'text': text,
        }],

        'export_data': {
            'data': {
                'excel': {
                    'value': text,
                },
            }
        },
    }


def get_comprehensive_data(_, *args):
    return _get_text(*args)
