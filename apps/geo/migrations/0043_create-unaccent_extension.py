# Generated by Django 3.2.17 on 2023-08-21 08:03

from django.db import migrations
from django.contrib.postgres.operations import CreateExtension

class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0042_rename_data_geoarea_cached_data'),
    ]

    operations = [
        CreateExtension('unaccent')
    ]
