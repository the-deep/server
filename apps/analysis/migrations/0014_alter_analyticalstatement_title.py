# Generated by Django 3.2.17 on 2024-04-03 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0013_auto_20240315_0501'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analyticalstatement',
            name='title',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]
