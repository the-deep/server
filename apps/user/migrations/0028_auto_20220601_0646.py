# Generated by Django 3.2.10 on 2022-06-01 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0027_alter_feature_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='deleted_at',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='old_display_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
