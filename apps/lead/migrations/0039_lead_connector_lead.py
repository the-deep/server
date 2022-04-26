# Generated by Django 3.2.10 on 2022-03-03 11:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('unified_connector', '0002_auto_20220303_1143'),
        ('lead', '0038_lead_extraction_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='connector_lead',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='unified_connector.connectorlead'),
        ),
    ]
