# Generated by Django 3.2.17 on 2024-03-11 08:56

from django.utils.crypto import get_random_string
from django.db import migrations, models


def generate_random_reference_id():
    return get_random_string(length=16)


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0014_alter_analysisreportcontainer_content_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysisreportcontainerdata',
            name='client_reference_id',
            # NOTE: This will not generate random values, we don't have much data before this migrations.
            # So, for now just ignoring.
            field=models.CharField(default=generate_random_reference_id, max_length=20),
            preserve_default=False,
        ),
    ]
