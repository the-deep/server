# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-01-26 06:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ary', '0031_auto_20181227_0506'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnderlyingFactor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('order', models.IntegerField(default=1)),
                ('parent', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='ary.UnderlyingFactor')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ary.AssessmentTemplate')),
            ],
            options={
                'ordering': ['order'],
                'abstract': False,
            },
        ),
    ]
