# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-24 11:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis_framework', '0006_auto_20171124_0629'),
    ]

    operations = [
        migrations.AddField(
            model_name='widget',
            name='key',
            field=models.CharField(default='asdasdasd', max_length=100),
            preserve_default=False,
        ),
    ]
