# Generated by Django 2.1.15 on 2020-09-11 05:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('connector', '0018_auto_20200904_0557'),
    ]

    operations = [
        migrations.AddField(
            model_name='unifiedconnector',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
