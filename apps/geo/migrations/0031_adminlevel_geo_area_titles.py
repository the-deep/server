# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-14 06:53
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0030_auto_20180912_1002'),
    ]

    operations = [
        migrations.AddField(
            model_name='adminlevel',
            name='geo_area_titles',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, null=True),
        ),
    ]