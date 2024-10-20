# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-03-22 09:16
from __future__ import unicode_literals

from django.db import migrations
from analysis_framework.utils import update_widgets
from entry.utils import update_attributes

def update_all(apps, schema_editor):
    """
    NOTE: This migration is out-of-date. Keeping it here for reference only.
    update_widgets()
    update_attributes()
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0008_auto_20180215_0850'),
    ]

    operations = [
        migrations.RunPython(update_all),
    ]
