# Generated by Django 3.2.10 on 2022-06-08 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('export', '0019_auto_20220511_0632'),
    ]

    operations = [
        migrations.AlterField(
            model_name='export',
            name='type',
            field=models.CharField(choices=[('entries', 'Entries'), ('assessments', 'Assessments'), ('planned_assessments', 'Planned Assessments'), ('analyses', 'Analysis')], max_length=99),
        ),
    ]
