# Generated by Django 3.2.17 on 2023-08-09 08:14

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment_registry', '0022_auto_20230809_0512'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessmentregistry',
            name='protection_info_mgmts',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(choices=[(100, 'Protection Monitoring'), (1, 'Protection Needs Assessment'), (2, 'Case Management'), (3, 'Population Data'), (4, 'Protection Response M&E'), (5, 'Communicating with(in) Affected Communities'), (6, 'Security & Situational Awareness'), (7, 'Sectoral System/Other')]), blank=True, default=list, size=None),
        ),
    ]
