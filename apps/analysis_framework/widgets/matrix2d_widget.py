WIDGET_ID = "matrix2dWidget"


"""
PROPERTIES:
    rows: [
        key: string
        label: string
        tooltip?: string
        order: number
        color: string
        subRows: [
            key: string
            label: string
            tooltip?: string
            order: number
        ]
    ]
    columns: [
        key: string
        label: string
        tooltip?: string
        order: number
        subColumns: [
            key: string
            label: string
            tooltip?: string
            order: number
        ]
    ]
}
"""


def get_filters(widget, properties):
    """
    Old <-> New
    dimensions <-> rows
    subdimensions <-> subRows
    sectors <-> columns
    subsectors <-> subColumns
    """
    from analysis_framework.models import Filter  # To avoid circular import

    row_options = []
    rows = properties.get("rows", [])

    for row in rows:
        row_options.append(
            {
                "label": row.get("label"),
                "key": row.get("key"),
            }
        )

        sub_rows = row.get("subRows", [])
        for sub_row in sub_rows:
            row_options.append(
                {
                    "label": "{} / {}".format(
                        row.get("label"),
                        sub_row.get("label"),
                    ),
                    "key": sub_row.get("key"),
                }
            )

    column_options = []
    columns = properties.get("columns", [])

    for column in columns:
        column_options.append(
            {
                "label": column.get("label"),
                "key": column.get("key"),
            }
        )

        subcolumns = column.get("subColumns", [])
        for subcolumn in subcolumns:
            column_options.append(
                {
                    "label": "{} / {}".format(
                        column.get("label"),
                        subcolumn.get("label"),
                    ),
                    "key": subcolumn.get("key"),
                }
            )

    return [
        {
            "title": "{} Rows".format(widget.title),
            "filter_type": Filter.FilterType.LIST,
            "key": "{}-rows".format(widget.key),
            "properties": {
                "type": "multiselect",
                "options": row_options,
            },
        },
        {
            "title": "{} Columns".format(widget.title),
            "filter_type": Filter.FilterType.LIST,
            "key": "{}-columns".format(widget.key),
            "properties": {
                "type": "multiselect",
                "options": column_options,
            },
        },
    ]


def get_exportable(widget, properties):
    excel = {
        "type": "multiple",
        "titles": [
            "{} - Row".format(widget.title),
            "{} - SubRow".format(widget.title),
            "{} - Column".format(widget.title),
            "{} - SubColumns".format(widget.title),
        ],
    }

    report = {
        "levels": [
            {
                "id": column.get("key"),
                "title": column.get("label"),
                "sublevels": [
                    {
                        "id": "{}-{}".format(
                            column.get("key"),
                            row.get("key"),
                        ),
                        "title": row.get("label"),
                        "sublevels": [
                            {
                                "id": "{}-{}-{}".format(
                                    column.get("key"),
                                    row.get("key"),
                                    sub_row.get("key"),
                                ),
                                "title": sub_row.get("label"),
                            }
                            for sub_row in row.get("subRows", [])
                        ],
                    }
                    for row in properties.get("rows", [])
                ],
            }
            for column in properties.get("columns", [])
        ],
    }

    return {
        "excel": excel,
        "report": report,
    }
