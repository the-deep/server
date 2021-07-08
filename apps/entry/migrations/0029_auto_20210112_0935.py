# Generated by Django 2.1.15 on 2021-01-12 09:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0028_auto_20200914_1146'),
    ]

    operations = [
        migrations.RenameField(
            model_name='entry',
            old_name='image',
            new_name='image_raw',
        ),
        migrations.AddField(
            model_name='entry',
            name='image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gallery.File'),
        ),
    ]