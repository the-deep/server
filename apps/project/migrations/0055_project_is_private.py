# Generated by Django 2.1.8 on 2019-06-17 11:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0054_auto_20181227_0506'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='is_private',
            field=models.BooleanField(default=False),
        ),
    ]
