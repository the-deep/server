# Generated by Django 3.2.25 on 2024-05-31 05:04

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0014_alter_analyticalstatement_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='automaticsummary',
            name='widget_tags',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), default=list, size=None),
        ),
        migrations.AddField(
            model_name='topicmodel',
            name='widget_tags',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), default=list, size=None),
        ),
    ]