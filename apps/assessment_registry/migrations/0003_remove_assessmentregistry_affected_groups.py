# Generated by Django 3.2.17 on 2023-07-13 06:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assessment_registry', '0002_auto_20230710_0533'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assessmentregistry',
            name='affected_groups',
        ),
    ]