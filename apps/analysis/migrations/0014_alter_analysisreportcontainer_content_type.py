# Generated by Django 3.2.17 on 2024-03-08 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0013_alter_analysisreportcontainer_content_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysisreportcontainer',
            name='content_type',
            field=models.SmallIntegerField(choices=[(1, 'Text'), (2, 'Heading'), (3, 'Image'), (4, 'URL'), (5, 'Timeline Chart'), (6, 'KPIs'), (7, 'Bar Chart'), (8, 'Map')]),
        ),
    ]
