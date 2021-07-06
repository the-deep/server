# Generated by Django 3.2 on 2021-07-06 08:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0005_auto_20210629_0732'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysis',
            name='cloned_from',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='analysis.analysis'),
        ),
        migrations.AddField(
            model_name='analysispillar',
            name='cloned_from',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='analysis.analysispillar'),
        ),
        migrations.AddField(
            model_name='analyticalstatement',
            name='cloned_from',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='analysis.analyticalstatement'),
        ),
    ]
