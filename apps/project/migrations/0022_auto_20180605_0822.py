# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-06-05 08:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0021_projectstatus_projectstatuscondition'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectstatuscondition',
            name='project_status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conditions', to='project.ProjectStatus'),
        ),
    ]