# Generated by Django 3.2.17 on 2024-03-14 04:22

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment_registry', '0048_auto_20240215_0642'),
    ]

    operations = [
        migrations.AddField(
            model_name='assessmentregistry',
            name='protection_risks',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(choices=[(1, 'Abduction, kidnapping, enforced disappearance, arbitrary or unlawful arrest and/or detention'), (2, 'Attacks on civilians and other unlawful killings, and attacks on civilian objects'), (3, 'Child and forced family separation'), (4, 'Child, early or forced marriage'), (5, 'Discrimination and stigmatization, denial of resources, opportunities, services and/or humanitarian access'), (6, 'Disinformation and denial of access to information'), (7, 'Forced recruitment and association of children in armed forces and groups'), (8, 'Gender-based violence'), (9, 'Impediments and/or restrictions to access to legal identity, remedies and justice'), (10, 'Presence of Mine and other explosive ordnance'), (11, 'Psychological/emotional abuse or inflicted distress'), (12, 'Theft, extortion, forced eviction or destruction of personal property'), (13, 'Torture or cruel, inhuman, degrading treatment or punishment'), (14, 'Trafficking in persons, forced labour or slavery-like practices'), (15, 'Unlawful impediments or restrictions to freedom of movement, siege and forced displacement')]), blank=True, default=list, size=None),
        ),
    ]
