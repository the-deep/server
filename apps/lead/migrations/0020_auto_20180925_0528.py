# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-25 05:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lead', '0019_auto_20180713_0733'),
    ]

    operations = [
        migrations.AddField(
            model_name='leadpreview',
            name='page_count',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='leadpreview',
            name='thumbnail',
            field=models.FileField(blank=True, default=None, null=True, upload_to='lead-thumbnail/'),
        ),
        migrations.AddField(
            model_name='leadpreview',
            name='word_count',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]