# Generated by Django 2.1.15 on 2020-09-14 11:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('entry', '0027_entry_verified'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='verification_last_changed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='entry',
            name='verified',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
