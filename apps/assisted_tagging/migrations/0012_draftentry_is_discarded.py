# Generated by Django 3.2.17 on 2023-12-11 05:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assisted_tagging', '0011_draftentry_draft_entry_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='draftentry',
            name='is_discarded',
            field=models.BooleanField(default=False),
        ),
    ]
