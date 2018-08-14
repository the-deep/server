# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-08-02 06:08
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0010_profile_receive_email'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='receive_email',
        ),
        migrations.AddField(
            model_name='profile',
            name='email_opt_outs',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('join_requests', 'Project join requests'), ('news_and_updates', 'News and updates')], max_length=128), default=[], size=None),
        ),
    ]
