# Generated by Django 2.1.13 on 2019-11-07 04:26

from django.db import migrations


def assign_source_objects_to_connectors(apps, schema_editor):
    ConnectorSource = apps.get_model('connector', 'ConnectorSource')
    Connector = apps.get_model('connector', 'Connector')

    sources = {x.key: x for x in ConnectorSource.objects.all()}

    for connector in Connector.objects.all():
        connector.source_obj = sources.get(connector.source)
        connector.save()


class Migration(migrations.Migration):

    dependencies = [
        ('connector', '0013_connector_source_obj'),
    ]

    operations = [
        migrations.RunPython(
            assign_source_objects_to_connectors,
            migrations.RunPython.noop,
        )
    ]
