# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-26 06:24
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tabular', '0005_auto_20181025_0634'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='meta',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='book',
            name='meta_status',
            field=models.CharField(choices=[('initial', 'Initial (Book Just Added)'), ('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')], default='initial', max_length=30),
        ),
    ]
