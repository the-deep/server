# Generated by Django 2.1.13 on 2019-11-18 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lead', '0029_merge_20190918_0941'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='emmentity',
            options={'ordering': ('name',)},
        ),
        migrations.AlterModelOptions(
            name='leademmtrigger',
            options={'ordering': ('-count',)},
        ),
        migrations.AddField(
            model_name='leadpreview',
            name='classification_status',
            field=models.CharField(choices=[('none', 'None'), ('initiated', 'Initiated'), ('completed', 'Completed'), ('failed', 'Failed'), ('errored', 'Errored')], default='none', max_length=20),
        ),
    ]
