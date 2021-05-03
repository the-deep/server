# Generated by Django 3.2 on 2021-05-03 04:31

from django.db import migrations, models
import project.models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0066_projectstats_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='data',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='stats_cache',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='projectjoinrequest',
            name='data',
            field=models.JSONField(blank=True, default=project.models.get_default_join_request_data, null=True),
        ),
    ]
