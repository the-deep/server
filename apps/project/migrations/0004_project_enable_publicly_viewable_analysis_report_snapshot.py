# Generated by Django 3.2.17 on 2023-10-06 04:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0003_auto_20230508_0608'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='enable_publicly_viewable_analysis_report_snapshot',
            field=models.BooleanField(default=False),
        ),
    ]
