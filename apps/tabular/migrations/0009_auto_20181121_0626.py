# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-21 06:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tabular', '0008_geodata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='gallery.File'),
        ),
    ]
