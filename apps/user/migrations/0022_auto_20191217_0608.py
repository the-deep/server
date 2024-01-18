# Generated by Django 2.1.8 on 2019-12-17 06:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0021_auto_20191111_1200'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feature',
            name='key',
            field=models.CharField(choices=[('private_project', 'Private projects'), ('tabular', 'Tabular'), ('zoomable_image', 'Zoomable image'), ('entry_visualization_configuration', 'Entry visualization configuration')], max_length=255, unique=True),
        ),
    ]