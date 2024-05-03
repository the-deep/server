# Generated by Django 3.2.17 on 2024-02-22 05:02
from django.db import migrations
import copy


def analysis_framework_widgets_mapping(apps, schema_editor):
    AnalysisFramework = apps.get_model('analysis_framework', 'AnalysisFramework')
    af_qs = AnalysisFramework.objects.filter(properties__isnull=False)
    for af in af_qs:
        if af.properties == {}:
            continue
        af_prop = af.properties
        # Remove super legacy config
        af_prop.pop('old_stats_config', None)

        # For reassurance
        old_stats_config = copy.deepcopy(af_prop)

        # Migrate legacy config to latest
        # -- Widget1D
        af_prop['stats_config']['widget_1d'] = (
            af_prop['stats_config'].get('widget_1d') or
            af_prop['stats_config'].get('widget1d') or
            []
        )

        # -- Widget2D
        af_prop['stats_config']['widget_2d'] = (
            af_prop['stats_config'].get('widget_2d') or
            af_prop['stats_config'].get('widget2d') or
            []
        )

        # -- Organigram
        af_prop['stats_config']['organigram_widgets'] = (
            af_prop['stats_config'].get('affected_groups_widget') or
            af_prop['stats_config'].get('organigram_widgets') or
            af_prop['stats_config'].get('organigram_widget') or
            []
        )

        # -- Multiselect
        af_prop['stats_config']['multiselect_widgets'] = (
            af_prop['stats_config'].get('specific_needs_groups_widget') or
            af_prop['stats_config'].get('multiselect_widgets') or
            af_prop['stats_config'].get('multiselect_widget') or
            af_prop['stats_config'].get('demographic_groups_widget') or
            []
        )

        legacy_widget_keys = [
            'widget1d',
            'widget2d',
            'affected_groups_widgets',
            'specific_needs_groups_widgets',
            'affected_groups_widget',
            'specific_needs_groups_widget',
            'demographic_group_widgets',
            'specificNeedsGroupsWidget',
        ]
        for widget_key in legacy_widget_keys:
            af_prop['stats_config'].pop(widget_key, None)

        af.properties = af_prop
        af.properties['old_stats_config'] = old_stats_config
        af.save(update_fields=('properties',))


class Migration(migrations.Migration):

    dependencies = [
        ('analysis_framework', '0040_auto_20231109_1208'),
    ]
    operations = [
        migrations.RunPython(
            analysis_framework_widgets_mapping,
            reverse_code=migrations.RunPython.noop
        )
    ]
