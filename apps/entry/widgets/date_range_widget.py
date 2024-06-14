from analysis_framework.widgets.date_range_widget import WIDGET_ID

from .date_widget import parse_date_str

# NOTE: Please update the data version when you update the data format
DATA_VERSION = 1


def _get_date(widget, data, widget_properties):
    value = data.get("value", {})
    from_value = value.get("startDate")  # TODO: use from
    to_value = value.get("endDate")  # TODO: use to

    from_date, from_number = parse_date_str(from_value)
    to_date, to_number = parse_date_str(to_value)

    # NOTE: Please update the data version when you update the data format
    return (
        from_number,
        to_number,
    ), (
        from_date,
        to_date,
    )


def update_attribute(widget, data, widget_properties):
    (from_number, to_number), (from_date, to_date) = _get_date(widget, data, widget_properties)

    return {
        # NOTE: Please update the data version when you update the data format
        "filter_data": [
            {
                "from_number": from_number,
                "to_number": to_number,
            }
        ],
        "export_data": {
            "data": {
                "common": {
                    "values": [from_date, to_date],
                    "widget_id": WIDGET_ID,
                    "widget_key": widget.key,
                    "version": DATA_VERSION,
                },
                "excel": {},
                "report": {},
            },
        },
    }


def get_comprehensive_data(_, *args):
    (from_date, to_date) = _get_date(*args)[1]
    return {
        "from": from_date,
        "to": to_date,
    }
