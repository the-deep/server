# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-27 10:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0049_projectrole_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectrole',
            name='title',
            field=models.CharField(max_length=255),
        ),
    ]
