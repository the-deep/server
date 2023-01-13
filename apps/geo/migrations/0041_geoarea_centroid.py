# Generated by Django 3.2.15 on 2023-01-13 14:55

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0040_region_cache_index'),
    ]

    operations = [
        migrations.AddField(
            model_name='geoarea',
            name='centroid',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
    ]
