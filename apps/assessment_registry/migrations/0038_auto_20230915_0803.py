# Generated by Django 3.2.17 on 2023-09-15 08:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assessment_registry', '0037_auto_20230912_1157'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='summaryfocus',
            name='total_affected',
        ),
        migrations.RemoveField(
            model_name='summaryfocus',
            name='total_not_affected',
        ),
        migrations.RemoveField(
            model_name='summaryfocus',
            name='total_people_critically_in_need',
        ),
        migrations.RemoveField(
            model_name='summaryfocus',
            name='total_people_in_need',
        ),
        migrations.RemoveField(
            model_name='summaryfocus',
            name='total_people_moderately_in_need',
        ),
        migrations.RemoveField(
            model_name='summaryfocus',
            name='total_people_severly_in_need',
        ),
        migrations.RemoveField(
            model_name='summaryfocus',
            name='total_pop_assessed',
        ),
    ]
