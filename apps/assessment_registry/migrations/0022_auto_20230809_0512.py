# Generated by Django 3.2.17 on 2023-08-09 05:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assessment_registry', '0021_auto_20230808_1125'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assessmentregistry',
            name='final_score',
        ),
        migrations.RemoveField(
            model_name='assessmentregistry',
            name='matrix_score',
        ),
    ]