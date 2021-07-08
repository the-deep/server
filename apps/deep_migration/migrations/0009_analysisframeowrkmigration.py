# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-01-15 06:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analysis_framework', '0015_auto_20180111_1049'),
        ('deep_migration', '0008_leadmigration'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnalysisFrameowrkMigration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_migrated_at', models.DateTimeField(auto_now_add=True)),
                ('last_migrated_at', models.DateTimeField(auto_now=True)),
                ('old_id', models.IntegerField(unique=True)),
                ('analysis_framework', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='analysis_framework.AnalysisFramework')),
            ],
            options={
                'ordering': ['-first_migrated_at'],
                'abstract': False,
            },
        ),
    ]