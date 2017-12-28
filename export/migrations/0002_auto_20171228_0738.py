# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-28 07:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('export', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='export',
            name='pending',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='export',
            name='format',
            field=models.CharField(blank=True, choices=[('xlsx', 'xlsx'), ('docx', 'docx'), ('pdf', 'pdf')], max_length=100),
        ),
        migrations.AlterField(
            model_name='export',
            name='title',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='export',
            name='type',
            field=models.CharField(blank=True, choices=[('entries', 'entries')], max_length=100),
        ),
    ]
