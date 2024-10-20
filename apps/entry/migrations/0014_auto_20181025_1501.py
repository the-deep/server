# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-25 15:01
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0013_auto_20180824_1018'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='data_series',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='entry',
            name='entry_type',
            field=models.CharField(choices=[('excerpt', 'Excerpt'), ('image', 'Image'), ('data_series', 'Data Series')], default='excerpt', max_length=10),
        ),
    ]
