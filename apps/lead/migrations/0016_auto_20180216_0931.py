# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-16 09:31
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lead', '0015_auto_20180115_0852'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='lead',
            options={'ordering': ['-created_at']},
        ),
    ]
