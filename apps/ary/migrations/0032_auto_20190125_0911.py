# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-01-25 09:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ary', '0031_auto_20181227_0506'),
    ]

    operations = [
        migrations.AddField(
            model_name='metadatafield',
            name='is_required',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='methodologyfield',
            name='is_required',
            field=models.BooleanField(default=True),
        ),
    ]
