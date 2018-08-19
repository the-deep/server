# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-08-19 10:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0035_auto_20180815_1014'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectjoinrequest',
            name='role',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='project.ProjectRole'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='projectmembership',
            name='role',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='project.ProjectRole'),
            preserve_default=False,
        ),
    ]
