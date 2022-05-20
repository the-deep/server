# Generated by Django 3.2.12 on 2022-05-20 04:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0074_projectrole_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='geo_cache_file',
            field=models.FileField(blank=True, null=True, upload_to=''),
        ),
        migrations.AddField(
            model_name='project',
            name='geo_cache_hash',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
