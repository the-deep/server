# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-13 11:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0032_auto_20180913_1100'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectusergroupmembership',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.Project'),
        ),
        migrations.AlterField(
            model_name='projectusergroupmembership',
            name='usergroup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_group.UserGroup'),
        ),
    ]
