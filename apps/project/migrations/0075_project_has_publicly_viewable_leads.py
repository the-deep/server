# Generated by Django 3.2.10 on 2022-04-13 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0074_projectrole_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='has_publicly_viewable_leads',
            field=models.BooleanField(default=False),
        ),
    ]
