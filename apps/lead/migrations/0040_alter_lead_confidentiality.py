# Generated by Django 3.2.12 on 2022-05-10 04:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lead', '0039_lead_connector_lead'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lead',
            name='confidentiality',
            field=models.CharField(choices=[('unprotected', 'Public'), ('restricted', 'Restricted'), ('confidential', 'Confidential')], default='unprotected', max_length=30),
        ),
    ]
