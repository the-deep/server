# Generated by Django 3.2.12 on 2022-05-18 08:28

import uuid
from django.db import migrations, models

from deep.managers import BulkUpdateManager


def gen_uuid(apps, _):
    LeadModel = apps.get_model('lead', 'Lead')
    bulk_mgr = BulkUpdateManager(
        ['uuid'],
        chunk_size=10000,
    )
    qs = LeadModel.objects.all()
    print(f'Leads to update: {qs.count()}')
    for lead in qs.only('id').iterator():
        lead.uuid = uuid.uuid4()
        bulk_mgr.add(lead)
    bulk_mgr.done()


class Migration(migrations.Migration):

    dependencies = [
        ('lead', '0042_lead_uuid'),
    ]

    operations = [
        migrations.RunPython(gen_uuid, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='lead',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
