# Generated by Django 3.2.17 on 2023-07-19 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment_registry', '0005_auto_20230719_0801'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='additionaldocument',
            name='executive_summary',
        ),
        migrations.AddField(
            model_name='assessmentregistry',
            name='executive_summary',
            field=models.TextField(blank=True),
        ),
    ]
