# Generated by Django 3.2.9 on 2021-12-12 08:22

from django.db import migrations, models


def set_lead_extraction_status_for_current_leads(apps, schema_editor):
    # From Lead.LeadExtractionStatus
    PENDING = 0
    SUCCESS = 2
    FAILED = 3
    Lead = apps.get_model('lead', 'Lead')
    Lead.objects.update(extraction_status=SUCCESS)
    Lead.objects.filter(leadpreview__isnull=True).update(extraction_status=PENDING)
    Lead.objects.filter(leadpreview__text_extract__isnull=True).update(extraction_status=FAILED)


class Migration(migrations.Migration):

    dependencies = [
        ('lead', '0037_auto_20210715_0432'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='extraction_status',
            field=models.SmallIntegerField(choices=[(0, 'Pending'), (1, 'Started'), (4, 'Retrying'), (2, 'Success'), (3, 'Failed')], default=0),
        ),
        migrations.RunPython(
            set_lead_extraction_status_for_current_leads,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
