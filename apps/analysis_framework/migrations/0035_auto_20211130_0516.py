# Generated by Django 3.2.9 on 2021-11-30 05:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analysis_framework', '0034_widget_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='widget',
            name='conditional_conditions',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='widget',
            name='conditional_parent_widget',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='child_widget_conditionals', to='analysis_framework.widget'),
        ),
    ]