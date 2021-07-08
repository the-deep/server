# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-21 05:49
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0013_auto_20171114_1117'),
    ]

    operations = [
        migrations.RenameField(
            model_name='region',
            old_name='data',
            new_name='regional_groups',
        ),
        migrations.AddField(
            model_name='region',
            name='key_figures',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='region',
            name='media_sources',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='region',
            name='population_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, null=True),
        ),
    ]