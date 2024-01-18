# Generated by Django 3.2.17 on 2023-07-19 08:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment_registry', '0004_assessmentregistry_affected_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='additionaldocument',
            name='executive_summary',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='additionaldocument',
            name='document_type',
            field=models.IntegerField(choices=[(0, 'Assessment database'), (1, 'Questionnaire'), (2, 'Miscellaneous')]),
        ),
    ]