# Generated by Django 2.1.10 on 2019-09-06 09:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lead', '0024_lead_author'),
        ('lead', '0025_auto_20190828_0949'),
    ]

    operations = [
        migrations.RenameField(
            model_name='lead',
            old_name='author',
            new_name='author_raw',
        ),
        migrations.RenameField(
            model_name='lead',
            old_name='source',
            new_name='source_raw',
        ),
    ]
