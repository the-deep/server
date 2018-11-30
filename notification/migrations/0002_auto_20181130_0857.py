# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-30 08:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notification',
            options={},
        ),
        migrations.RemoveField(
            model_name='notification',
            name='client_id',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='modified_at',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='modified_by',
        ),
        migrations.AddField(
            model_name='notification',
            name='timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[('project_join_request', 'Join project request'), ('project_join_response', 'Join project response')], max_length=48),
        ),
        migrations.AlterField(
            model_name='notification',
            name='status',
            field=models.CharField(choices=[('seen', 'Seen'), ('unseen', 'Unseen')], default='unseen', max_length=48),
        ),
    ]
