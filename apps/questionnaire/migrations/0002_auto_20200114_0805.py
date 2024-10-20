# Generated by Django 2.1.8 on 2020-01-14 08:05

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='frameworkquestion',
            name='label',
            field=models.CharField(blank=True, max_length=256),
        ),
        migrations.AddField(
            model_name='frameworkquestion',
            name='response_options',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='label',
            field=models.CharField(blank=True, max_length=256),
        ),
        migrations.AddField(
            model_name='question',
            name='response_options',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='frameworkquestion',
            name='data_collection_technique',
            field=models.CharField(blank=True, choices=[('direct', 'Direct observation'), ('focus_group', 'Focus group'), ('one_on_one_interviews', '1-on-1 interviews'), ('open_ended_survey', 'Open-ended survey'), ('closed_ended_survey', 'Closed-ended survey')], max_length=56),
        ),
        migrations.AlterField(
            model_name='question',
            name='data_collection_technique',
            field=models.CharField(blank=True, choices=[('direct', 'Direct observation'), ('focus_group', 'Focus group'), ('one_on_one_interviews', '1-on-1 interviews'), ('open_ended_survey', 'Open-ended survey'), ('closed_ended_survey', 'Closed-ended survey')], max_length=56),
        ),
        migrations.AlterField(
            model_name='questionnaire',
            name='data_collection_technique',
            field=models.CharField(blank=True, choices=[('direct', 'Direct observation'), ('focus_group', 'Focus group'), ('one_on_one_interviews', '1-on-1 interviews'), ('open_ended_survey', 'Open-ended survey'), ('closed_ended_survey', 'Closed-ended survey')], max_length=56),
        ),
    ]
