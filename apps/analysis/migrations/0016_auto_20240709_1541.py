# Generated by Django 3.2.25 on 2024-07-09 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0015_auto_20240531_0504'),
    ]

    operations = [
        migrations.AddField(
            model_name='automaticsummary',
            name='information_gap',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='automaticsummary',
            name='analytical_statement',
            field=models.TextField(blank=True),
        ),
    ]