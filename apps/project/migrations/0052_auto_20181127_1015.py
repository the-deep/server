# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-27 10:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0051_auto_20181127_1005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectrole',
            name='title',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]