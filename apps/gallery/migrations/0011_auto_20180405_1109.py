# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-04-05 11:09
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0010_auto_20180216_0931'),
    ]

    operations = [
        migrations.RenameField(
            model_name='file',
            old_name='meta_data',
            new_name='metadata',
        ),
    ]