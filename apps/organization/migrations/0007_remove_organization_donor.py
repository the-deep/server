# Generated by Django 2.1.8 on 2019-05-17 04:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0006_auto_20190425_0510'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organization',
            name='donor',
        ),
    ]