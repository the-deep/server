# Generated by Django 3.2.15 on 2022-12-04 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis_framework', '0037_analysisframework_assisted_tagging_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysisframework',
            name='export',
            field=models.FileField(blank=True, default=None, max_length=255, null=True, upload_to='af-exports/'),
        ),
    ]
