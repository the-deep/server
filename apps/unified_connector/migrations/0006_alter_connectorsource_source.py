# Generated by Django 3.2.12 on 2022-05-20 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unified_connector', '0005_auto_20220426_0906'),
    ]

    operations = [
        migrations.AlterField(
            model_name='connectorsource',
            name='source',
            field=models.CharField(choices=[('atom-feed', 'Atom Feed'), ('relief-web', 'Relifweb'), ('rss-feed', 'RSS Feed'), ('unhcr-portal', 'UNHCR Portal'), ('humanitarian-resp', 'Humanitarian Response'), ('pdna', 'Post Disaster Needs Assessments')], max_length=20),
        ),
    ]
