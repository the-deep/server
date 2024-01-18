# Generated by Django 3.2.17 on 2023-05-08 06:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0002_projectchangelog'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='last_read_access',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='last_write_access',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]