from django.contrib.gis.db.models import Extent
from django.utils import timezone
from django.db.models import Prefetch

from geo.models import GeoArea
from analysis_framework.models import Widget, Filter

from .models import Entry, Attribute

SUPPORTED_WIDGETS = [
    'matrix1dWidget', 'matrix2dWidget', 'scaleWidget', 'multiselectWidget', 'organigramWidget', 'geoWidget',
    'conditionalWidget',
]


def _get_widget_info(config, widgets, widget_name, skip_data=False):
    widget = widgets[config[widget_name]['pk']]

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
                analysis_framework_id=widget.analysis_framework_id,
            ).first()
        )

    data = widget.properties['data']
    # TODO: Add validator for this
    selectors = config[widget_name].get('selectors')
    if selectors:
        for selector in selectors + ['properties', 'data']:
            data = data[selector]
    return _return(data)


def _get_attribute_data(collector, attribute, cd_widget_map):

    def _get_widget_value(w_value, widget_type, widget_pk=None):
        value = None
        if widget_type in ['scaleWidget', 'multiselectWidget', 'organigramWidget', 'geoWidget']:
            value = w_value
        elif widget_type == 'conditionalWidget':
            cd_config = cd_widget_map.get(widget_pk)
            if cd_config is not None:
                selected_widget_key = cd_config['widget_key']
                selected_widget_type = cd_config['widget_type']
                selected_widget_pk = cd_config.get('widget_pk')
                if w_value.get(selected_widget_key):
                    value = _get_widget_value(
                        w_value[selected_widget_key]['data']['value'],
                        selected_widget_type,
                        selected_widget_pk,
                    )
        elif widget_type in ['matrix1dWidget', 'matrix2dWidget']:
            context_keys = [
                f'{widget_pk}-{_value}'
                for _value in (
                    w_value.keys() if isinstance(w_value, dict) else []
                )
            ]
            sectors_keys = []
            if widget_type == 'matrix2dWidget':  # Collect sector data from here
                for pillar_key, pillar in w_value.items():
                    for subpillar_key, subpillar in pillar.items():
                        for sector_key in subpillar.keys():
                            sectors_keys.append([
                                f'{widget_pk}-{pillar_key}',
                                subpillar_key, sector_key,
                            ])
            value = {
                'context_keys': context_keys,
                'sectors_keys': sectors_keys,
            }
        return value

    widget_type = attribute.widget.widget_id
    widget_pk = attribute.widget.pk
    data = attribute.data

    if widget_type not in SUPPORTED_WIDGETS or data is None or data.get('value') is [None, {}, []]:
        return

    collector[widget_pk] = _get_widget_value(data['value'], widget_type, widget_pk)


def get_project_entries_stats(project):
    """
    NOTE: This is a custom API made for Entries VIz and only works for certain AF.

    # Sample config
    default_config = {
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
            'is_conditional_widget': True,
            'selectors': ['widgets', 0, 'widget'],
            'widget_key': 'scalewidget-ljlk28coxz7sufml',
            # TODO: Add validation here
            'widget_type': 'scaleWidget',
            'widget_pk': None,  # Required if widget_type is matrix
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
    """

    config = project.analysis_framework.properties.get('stats_config')

    widgets_pk = [info['pk'] for info in config.values()]
    cd_widget_map = {
        w_config['pk']: w_config for w_config in config.values() if w_config.get('is_conditional_widget')
    }
    widgets = {
        widget.pk: widget
        for widget in Widget.objects.filter(pk__in=widgets_pk)
    }

    w1d = _get_widget_info(config, widgets, 'widget_1d')
    w2d = _get_widget_info(config, widgets, 'widget_2d')
    w_specific_needs_groups = _get_widget_info(config, widgets, 'specific_needs_groups_widget')
    w_severity = _get_widget_info(config, widgets, 'severity_widget')
    w_reliability = _get_widget_info(config, widgets, 'reliability_widget')
    w_ag = _get_widget_info(config, widgets, 'affected_groups_widget')
    w_geo = _get_widget_info(config, widgets, 'geo_widget', skip_data=True)

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
        } for option in w_ag['data'].properties['options']
    ]
    specific_needs_groups_array = [
        {
            'id': option['key'],
            'name': option['label'],
        } for option in w_specific_needs_groups['data']['options']
    ]
    severity_units = [
        {
            'id': severity['key'],
            'color': severity['color'],
            'name': severity['label'],
        } for severity in w_severity['data']['scale_units']
    ]
    reliability_units = [
        {
            'id': reliability['key'],
            'color': reliability['color'],
            'name': reliability['label'],
        } for reliability in w_reliability['data']['scale_units']
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

    meta = {
        'data_calculated': timezone.now(),
        'context_array': context_array,
        'framework_groups_array': framework_groups_array,
        'sector_array': sector_array,
        'affected_groups_array': affected_groups_array,
        'specific_needs_groups_array': specific_needs_groups_array,
        'severity_units': severity_units,
        'reliability_units': reliability_units,
        'geo_array': geo_array,
    }

    data = []
    entries = Entry.objects.filter(project=project).prefetch_related(
        Prefetch(
            'attribute_set',
            queryset=Attribute.objects.filter(widget_id__in=widgets_pk),
        ),
        'attribute_set__widget',
    )
    for entry in entries.all():
        collector = {}
        for attribute in entry.attribute_set.all():
            _get_attribute_data(collector, attribute, cd_widget_map)

        data.append({
            'pk': entry.pk,
            'date': entry.created_at,
            'severity': collector.get(w_severity['pk']),
            'reliability': collector.get(w_reliability['pk']),
            'geo': collector.get(w_geo['pk'], []),
            'special_needs': collector.get(w_specific_needs_groups['pk'], []),
            'affected_groups': collector.get(w_ag['pk'], []),
            'context': (
                collector.get(w1d['pk'], {}).get('context_keys', []) +
                collector.get(w2d['pk'], {}).get('context_keys', [])
            ),
            'sector': (
                collector.get(w1d['pk'], {}).get('sectors_keys', []) +
                collector.get(w2d['pk'], {}).get('sectors_keys', [])
            ),
        })

    return {
        'meta': meta,
        'data': data,
    }
