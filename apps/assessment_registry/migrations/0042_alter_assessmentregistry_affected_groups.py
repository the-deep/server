# Generated by Django 3.2.17 on 2023-11-21 06:37

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment_registry', '0041_alter_scorerating_score_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessmentregistry',
            name='affected_groups',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(choices=[(1, 'All'), (2, 'All/Affected'), (3, 'All/Not Affected'), (4, 'All/Affected/Not Displaced'), (5, 'All/Affected/Displaced'), (6, 'All/Affected/Displaced/In Transit'), (7, 'All/Affected/Displaced/Migrants'), (8, 'All/Affected/Displaced/IDPs'), (9, 'All/Affected/Displaced/Asylum Seeker'), (10, 'All/Affected/Displaced/Other of concerns'), (11, 'All/Affected/Displaced/Returnees'), (12, 'All/Affected/Displaced/Refugees'), (13, 'All/Affected/Displaced/Migrants/In transit'), (14, 'All/Affected/Displaced/Migrants/Permanents'), (15, 'All/Affected/Displaced/Migrants/Pendular'), (16, 'All/Affected/Not Displaced/Not Host'), (17, 'All/Affected/Not Displaced/Host')]), default=list, size=None),
        ),
    ]
