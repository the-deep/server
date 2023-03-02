# Generated by Django 3.2.15 on 2023-02-28 08:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lead', '0046_auto_20230120_0543'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lead',
            name='duplicate_leads',
        ),
        migrations.AddField(
            model_name='lead',
            name='duplicate_leads_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
