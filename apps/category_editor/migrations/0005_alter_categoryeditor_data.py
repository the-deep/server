# Generated by Django 3.2 on 2021-05-03 04:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('category_editor', '0004_categoryeditor_client_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categoryeditor',
            name='data',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
    ]
