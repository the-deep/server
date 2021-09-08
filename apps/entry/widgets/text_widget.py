from analysis_framework.widgets.text_widget import WIDGET_ID


DATA_VERSION = 1


def _get_text(widget, data, widget_data):
    return str(
        data.get('value') or ''
    )


def update_attribute(*args, **kwargs):
    text = _get_text(*args, **kwargs)
    widget = args[0]

    return {
        'filter_data': [{
            'text': text,
        }],

        'export_data': {
            'data': {
                'common': {
                    'widget_id': WIDGET_ID,
                    'widget_key': widget.key,
                    'version': DATA_VERSION,
                },
                'excel': {
                    'value': text,
                },
            }
        },
    }


def get_comprehensive_data(_, *args):
    return _get_text(*args)
