# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-08-02 06:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('connector', '0002_auto_20180713_0733'),
    ]

    operations = [
        migrations.AlterField(
            model_name='connector',
            name='source',
            field=models.CharField(choices=[('rss-feed', 'RSS Feed'), ('acaps-briefing-notes', 'ACAPS Briefing Notes'), ('unhcr-portal', 'UNHCR Portal'), ('relief-web', 'ReliefWeb Reports')], max_length=96),
        ),
    ]
