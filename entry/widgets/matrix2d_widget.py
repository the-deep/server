from .utils import set_filter_data, set_export_data


def update_attribute(entry, widget, data, widget_data):
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

    set_filter_data(
        entry,
        widget,
        key='{}-dimensions'.format(widget.key),
        values=filter1_values,
    )
    set_filter_data(
        entry,
        widget,
        key='{}-sectors'.format(widget.key),
        values=filter2_values,
    )
    set_export_data(
        entry,
        widget,
        {
            'excel': {
                'type': 'lists',
                'values': excel_values,
            },
            'report': {
                'keys': report_values,
            },
        },
    )
