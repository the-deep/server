# Generated by Django 3.2.17 on 2023-07-28 08:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment_registry', '0009_assessmentregistry_locations'),
    ]

    operations = [
        migrations.AddField(
            model_name='additionaldocument',
            name='file_path',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]