# Generated by Django 2.1.15 on 2020-12-22 08:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('export', '0010_auto_20200106_0909'),
    ]

    operations = [
        migrations.AddField(
            model_name='export',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
    ]
