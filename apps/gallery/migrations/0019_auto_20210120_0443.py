# Generated by Django 2.1.15 on 2021-01-20 04:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0018_auto_20191217_0608'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='is_public',
            field=models.BooleanField(default=False),
        ),
    ]