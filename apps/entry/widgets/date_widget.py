from analysis_framework.widgets.date_widget import WIDGET_ID
from dateutil.parser import parse as date_parse

from utils.common import ONE_DAY, deep_date_format

# NOTE: Please update the data version when you update the data format
# this is tallied against the version stored in the export json data
DATA_VERSION = 1


def parse_date_str(value):
    date = value and date_parse(value)
    number = date and int(date.timestamp() / ONE_DAY)
    # NOTE: Please update the data version when you update the data format
    return deep_date_format(date, fallback=None), number


def _get_date(widget, data, widget_properties):
    value = data.get("value")
    return parse_date_str(value)


def update_attribute(widget, data, widget_properties):
    date, number = _get_date(widget, data, widget_properties)

    return {
        # NOTE: Please update the data version when you update the data format
        "filter_data": [
            {
                "number": number,
            }
        ],
        "export_data": {
            "data": {
                "common": {
                    "value": date,
                    "widget_id": WIDGET_ID,
                    "widget_key": widget.key,
                    "version": DATA_VERSION,
                },
                "excel": {},
                "report": {},
            }
        },
    }


def get_comprehensive_data(_, *args):
    return _get_date(*args)[0]
