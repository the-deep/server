# Generated by Django 3.2.12 on 2022-07-27 08:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0010_organizationtype_short_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='source',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(0, 'Web info extract VIEW'), (1, 'Web Info Data VIEW'), (2, 'Connector')], null=True),
        ),
    ]