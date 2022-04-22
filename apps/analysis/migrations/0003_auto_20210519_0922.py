# Generated by Django 2.1.15 on 2021-05-19 09:22

import analysis.models
from django.db import migrations, models
import django.db.models.deletion
import django_enumfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0029_auto_20210112_0935'),
        ('analysis', '0002_auto_20210409_1021'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscardedEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.IntegerField(choices=[(0, 'Redundant'), (1, 'Too old'), (2, 'Anecdotal'), (3, 'Outlier')])),
                ('analysis_pillar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analysis.AnalysisPillar')),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='entry.Entry')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='discardedentry',
            unique_together={('entry', 'analysis_pillar')},
        ),
    ]