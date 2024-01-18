# Generated by Django 3.2.5 on 2021-10-27 09:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0073_alter_projectjoinrequest_unique_together'),
        ('export', '0015_merge_20210603_0624'),
    ]

    operations = [
        migrations.AlterField(
            model_name='export',
            name='export_type',
            field=models.CharField(choices=[('excel', 'Excel'), ('report', 'Report'), ('json', 'Json')], max_length=100),
        ),
        migrations.AlterField(
            model_name='export',
            name='filters',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='export',
            name='format',
            field=models.CharField(choices=[('xlsx', 'xlsx'), ('docx', 'docx'), ('pdf', 'pdf'), ('json', 'json')], max_length=100),
        ),
        migrations.AlterField(
            model_name='export',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.project'),
        ),
        migrations.AlterField(
            model_name='export',
            name='title',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='export',
            name='type',
            field=models.CharField(choices=[('entries', 'Entries'), ('assessments', 'Assessments'), ('planned_assessments', 'Planned Assessments')], max_length=99),
        ),
    ]