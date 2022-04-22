# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-10 06:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('gallery', '0012_auto_20180507_0913'),
        ('geo', '0028_auto_20180330_0953'),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('short_name', models.CharField(blank=True, max_length=255)),
                ('long_name', models.CharField(blank=True, max_length=512)),
                ('country', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='geo.Region')),
                ('logo', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gallery.File')),
            ],
        ),
        migrations.CreateModel(
            name='OrganizationType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='organization',
            name='organization_type',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='organization.OrganizationType'),
        ),
    ]