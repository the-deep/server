from datetime import datetime
from .utils import set_filter_data, set_export_data


ONE_DAY = 24 * 60 * 60 * 1000


def update_attribute(entry, widget, data):
    value = data.get('value')
    if not value:
        return

    date = datetime.strptime(value, '%Y-%m-%d')

    number = int(date.timestamp() / ONE_DAY)
    set_filter_data(
        entry,
        widget,
        number=number,
    )

    set_export_data(
        entry,
        widget,
        {
            'excel': {
                'value': date.strftime('%d-%m-%Y'),
            },
        },
    )
