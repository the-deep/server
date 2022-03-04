# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-20 09:02
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0005_auto_20170907_1204'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='adminlevel',
            name='shape',
        ),
        migrations.AddField(
            model_name='adminlevel',
            name='geo_shape',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, null=True),
        ),
        migrations.DeleteModel(
            name='GeoShape',
        ),
    ]