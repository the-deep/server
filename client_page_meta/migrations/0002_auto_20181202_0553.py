# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-12-02 05:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client_page_meta', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='help_url',
            field=models.TextField(),
        ),
    ]
