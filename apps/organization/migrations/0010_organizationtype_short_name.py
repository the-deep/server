# Generated by Django 2.1.15 on 2020-11-13 05:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0009_auto_20191111_0845'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationtype',
            name='short_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
