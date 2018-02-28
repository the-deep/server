# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-28 06:56
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0025_auto_20180124_1100'),
    ]

    operations = [
        migrations.AlterField(
            model_name='geoarea',
            name='polygons',
            field=django.contrib.gis.db.models.fields.GeometryField(blank=True, default=None, null=True, srid=4326),
        ),
    ]
