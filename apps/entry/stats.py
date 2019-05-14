from django.contrib.gis.db.models import Extent

from geo.models import GeoArea
from analysis_framework.models import Widget, Filter

from .models import Entry


def get_widget_data(config, widget_name, skip_data=False):
    widget = Widget.objects.get(pk=config[widget_name]['pk'])

    def _return(data):
        return {
            '_widget': widget,
            'pk': widget.pk,
            'config': config[widget_name],
            'data': data,
        }

    if skip_data:
        return _return(None)

    if widget.widget_id == 'organigramWidget':
        return _return(
            Filter.objects.filter(
                widget_key=widget.key,
                analysis_framework=widget.analysis_framework,
            ).first()
        )

    data = widget.properties['data']
    selectors = config[widget_name].get('selectors')
    if selectors:
        for selector in selectors + ['properties', 'data']:
            data = data[selector]
    return _return(data)


CALC_SUPPORTED_WIDGETS = [
    'matrix1dWidget', 'matrix2dWidget', 'scaleWidget', 'multiselectWidget', 'organigramWidget', 'geoWidget',
    'conditionalWidget',
]


def _get_entry_widget_data(counts, widget, options):
    key = widget['widget'].key
    if widget['widget'].widget_id == 'conditionalWidget':
        key = widget['config']['key']
    return [
        counts.get('{}-{}'.format(key, element['id']), 0)
        for element in options
    ]


def calc_widget_count(selected_sector, entry_counts, counts, data, widget_type, widget_key):
    # print('{} ==> {}'.format(widget_type, data.get('value') if data else None))
    if widget_type not in CALC_SUPPORTED_WIDGETS or data is None or data.get('value') is [None, {}, []]:
        return

    value = data['value']
    keys = []
    if widget_type in ['matrix1dWidget', 'matrix2dWidget']:
        keys = value.keys() if isinstance(value, dict) else []
        if widget_type == 'matrix2dWidget':  # Collect sector data from here
            for pillar_key, pillar in value.items():
                for subpillar_key, subpillar in pillar.items():
                    for sector_key in subpillar.keys():
                        if sector_key not in selected_sector:
                            selected_sector.append(sector_key)

            # entry_counts
    elif widget_type == 'scaleWidget':
        keys = [value]
    elif widget_type in ['multiselectWidget', 'organigramWidget', 'geoWidget']:
        keys = value
    elif widget_type == 'conditionalWidget':
        selected_widget_key = value.get('selected_widget_key')
        widget_key = selected_widget_key
        if value.get(selected_widget_key):
            value = value[selected_widget_key]['data']['value']
            keys = value or [] if isinstance(value, list) else [value]

    for key in keys:
        count_key = '{}-{}'.format(widget_key, key)
        entry_counts[count_key] = counts[count_key] = counts.get(count_key, 0) + 1


def get_entries_viz_data(project):
    """
    NOTE: This is a custom API made for Entries VIz and only works for certain projects.
    """
    entries = Entry.objects.filter(project=project)

    # config = project.analysis_framework.properties.get('stats_config', {})
    config = {
        'widget_1d': {
            'pk': 2679,
        },
        'widget_2d': {
            'pk': 2676,
        },
        'geo_widget': {
            'pk': 2677,
        },
        'severity_widget': {
            'pk': 2902,
            'selectors': ['widgets', 0, 'widget'],
            'key': 'scalewidget-ljlk28coxz7sufml',
        },
        'reliability_widget': {
            'pk': 2683,
        },
        'affected_groups_widget': {
            'pk': 2682,
        },
        'specific_needs_groups_widget': {
            'pk': 2681,
        },
    }

    widgets_pk = [info['pk'] for info in config.values()]

    w1d = get_widget_data(config, 'widget_1d')
    w2d = get_widget_data(config, 'widget_2d')
    specific_needs_groups_w = get_widget_data(config, 'specific_needs_groups_widget')
    severity_w = get_widget_data(config, 'severity_widget')
    reliability_w = get_widget_data(config, 'reliability_widget')
    ag_w = get_widget_data(config, 'affected_groups_widget')

    context_array = [
        {
            'id': f"{w['pk']}-{dimension[id_key]}",
            'name': dimension['title'],
            'color': dimension['color'],
        } for id_key, w, dimensions in [
            ('key', w1d, w1d['data']['rows']),
            ('id', w2d, w2d['data']['dimensions']),
        ] for dimension in dimensions
    ]
    framework_groups_array = [
        {
            'id': subdimension['id'],
            'context_id': f"{w2d['pk']}-{dimension['id']}",
            'name': subdimension['title'],
            'tooltip': subdimension['tooltip'],
        } for dimension in w2d['data']['dimensions']
        for subdimension in dimension['subdimensions']
    ]

    sector_array = [
        {
            'id': sector['id'],
            'name': sector['title'],
            'tooltip': sector['tooltip'],
        } for sector in w2d['data']['sectors']
    ]
    affected_groups_array = [
        {
            'id': option['key'],
            'name': option['label'],
        } for option in ag_w['data'].properties['options']
    ]
    specific_needs_groups_array = [
        {
            'id': option['key'],
            'name': option['label'],
        } for option in specific_needs_groups_w['data']['options']
    ]
    severity_units = [
        {
            'id': severity['key'],
            'color': severity['color'],
            'name': severity['label'],
        } for severity in severity_w['data']['scale_units']
    ]
    reliability_units = [
        {
            'id': reliability['key'],
            'color': reliability['color'],
            'name': reliability['label'],
        } for reliability in reliability_w['data']['scale_units']
    ]

    geo_array = []
    for geoarea in GeoArea.objects.filter(
            admin_level__region__in=project.regions.values_list('id'),
    ).annotate(extent=Extent('polygons')).values('pk', 'admin_level__level', 'title', 'polygons', 'extent'):
        polygons = geoarea['polygons']
        centroid = polygons.centroid
        geo_array.append({
            'id': geoarea['pk'],
            'admin_level': geoarea['admin_level__level'],
            'name': geoarea['title'],
            'centroid': [centroid.x, centroid.y],
            'bounds': [geoarea['extent'][:2], geoarea['extent'][2:]],
        })

    """
    widget_to_support = [
        widget.widget_id
        for widget in [
            w1d, w2d,
            ag_w, specific_needs_groups_w,
            severity_w, reliability_w,
        ]
    ]

    if set(widget_to_support) != set(CALC_SUPPORTED_WIDGETS):
        for widget in widget_to_support:
            if widget not in CALC_SUPPORTED_WIDGETS:
                print('>> This widget should be supported -> {}'.format(widget))
    """

    data = []
    for entry in entries.all():
        for attribute in entry.attributes_set.filter(widget__pk_in=widgets_pk):
            pass
        data.append({
            'date': entry.created_at,
        })

    return {
        'meta_data': {
            'total_entries': entries.count(),
            'context_array': context_array,
            'framework_groups_array': framework_groups_array,
            'sector_array': sector_array,
            'geo_array': geo_array,
            'affected_groups_array': affected_groups_array,
            'specific_needs_groups_array': specific_needs_groups_array,
            'severity_units': severity_units,
            'reliability_units': reliability_units,
        },
        'data': data,
    }
