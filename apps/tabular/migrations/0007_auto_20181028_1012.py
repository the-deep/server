# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-28 10:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0044_auto_20181012_0653'),
        ('tabular', '0006_auto_20181026_0624'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='project',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='project.Project'),
        ),
        migrations.AlterField(
            model_name='field',
            name='type',
            field=models.CharField(choices=[('number', 'Number'), ('string', 'String'), ('datetime', 'Datetime'), ('geo', 'Geo')], default='string', max_length=30),
        ),
    ]
