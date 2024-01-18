# Generated by Django 3.2 on 2021-05-03 04:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis_framework', '0029_auto_20200117_0853'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysisframework',
            name='properties',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AlterField(
            model_name='exportable',
            name='data',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='filter',
            name='properties',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='widget',
            name='properties',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
    ]