# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-12-30 07:07
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tabular', '0009_auto_20181121_0626'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sheet',
            name='data',
        ),
    ]
