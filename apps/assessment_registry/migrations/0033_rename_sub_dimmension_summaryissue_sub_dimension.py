# Generated by Django 3.2.17 on 2023-08-23 06:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assessment_registry', '0032_auto_20230823_0635'),
    ]

    operations = [
        migrations.RenameField(
            model_name='summaryissue',
            old_name='sub_dimmension',
            new_name='sub_dimension',
        ),
    ]
