# Generated by Django 2.1.10 on 2019-12-02 08:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0058_projectarystats'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectarystats',
            name='modified_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='projectentrystats',
            name='modified_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
