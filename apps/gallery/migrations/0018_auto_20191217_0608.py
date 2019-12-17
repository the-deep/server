# Generated by Django 2.1.8 on 2019-12-17 06:08

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0017_uuid_unique_20190802_0921'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
