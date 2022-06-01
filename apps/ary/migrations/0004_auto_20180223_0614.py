# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-23 06:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ary', '0003_auto_20180223_0610'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='affectedgroup',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='assessmenttopic',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='metadatafield',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='metadatagroup',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='metadataoption',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='methodologyfield',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='methodologygroup',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='methodologyoption',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='affectedgroup',
            name='order',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='assessmenttopic',
            name='order',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='metadatafield',
            name='order',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='metadatagroup',
            name='order',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='metadataoption',
            name='order',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='methodologyfield',
            name='order',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='methodologygroup',
            name='order',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='methodologyoption',
            name='order',
            field=models.IntegerField(default=1),
        ),
    ]