# Generated by Django 3.2.10 on 2022-03-09 04:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assisted_tagging', '0005_auto_20220309_0446'),
        ('entry', '0035_alter_filterdata_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='draft_entry',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='assisted_tagging.draftentry'),
        ),
    ]
