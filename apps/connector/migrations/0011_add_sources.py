# Generated by Django 2.1.13 on 2019-11-05 08:27

from django.db import migrations


def kebab_to_title(kebab_str):
    return ' '.join([x.title() for x in kebab_str.split('-')])


def create_connector_sources(apps, schema_editor):
    ConnectorSource = apps.get_model('connector', 'ConnectorSource')
    for connector_key in [
            'atom-feed', 'rss-feed', 'emm', 'acaps-briefing-notes',
            'unhcr-portal', 'relief-web', 'post-disaster-needs-assessment',
            'research-resource-center', 'world-food-programme',
            'humanitarian-response',
    ]:
        ConnectorSource.objects.create(
            key=connector_key,
            name=kebab_to_title(connector_key),
        )


def remove_connector_sources(apps, schema_editor):
    ConnectorSource = apps.get_model('connector', 'ConnectorSource')
    ConnectorSource.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('connector', '0010_connectorsource'),
    ]

    operations = [
        migrations.RunPython(create_connector_sources, remove_connector_sources),
    ]
