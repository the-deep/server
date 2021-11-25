
# Generated by Django 3.2.5 on 2021-11-25 05:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0034_attribute_widget_version'),
        ('quality_assurance', '0002_entryreviewcomment_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='entryreviewcomment',
            name='entry_comment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='entry.entrycomment'),
        ),
    ]

