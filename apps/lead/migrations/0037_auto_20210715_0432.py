# Generated by Django 3.2 on 2021-07-15 04:32

from django.db import migrations


def _set_lead_is_assessment(Lead):
    # Set is_assessment_lead True for lead already having assessment.
    Lead.objects.filter(assessment__isnull=False).update(is_assessment_lead=True)


def set_lead_is_assessment(apps, schema_editor):
    Lead = apps.get_model('lead', 'Lead')
    _set_lead_is_assessment(Lead)


class Migration(migrations.Migration):

    dependencies = [
        ('lead', '0036_lead_is_assessment_lead'),
    ]

    operations = [
        migrations.RunPython(
            set_lead_is_assessment,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
