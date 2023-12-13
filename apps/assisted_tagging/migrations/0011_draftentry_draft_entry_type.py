# Generated by Django 3.2.17 on 2023-11-06 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assisted_tagging', '0010_draftentry_related_geoareas'),
    ]

    operations = [
        migrations.AddField(
            model_name='draftentry',
            name='draft_entry_type',
            field=models.SmallIntegerField(choices=[(0, 'Auto Extraction'), (1, 'Manual Extraction')], default=1),
        ),
    ]