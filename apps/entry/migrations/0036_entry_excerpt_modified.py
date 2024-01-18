# Generated by Django 3.2.10 on 2022-03-25 06:38

from django.db import migrations, models


def _update_entry_excerpt(Entry):
    Entry.objects\
        .exclude(
            models.Q(dropped_excerpt='') |
            models.Q(dropped_excerpt=models.F('excerpt'))
        ).update(excerpt_modified=True)
    Entry.objects\
        .filter(dropped_excerpt='')\
        .exclude(excerpt='')\
        .update(dropped_excerpt=models.F('excerpt'), excerpt_modified=False)


def update_entry_excerpt(apps, _):
    Entry = apps.get_model('entry', 'Entry')
    _update_entry_excerpt(Entry)


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0035_alter_filterdata_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='excerpt_modified',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(
            update_entry_excerpt,
            reverse_code=migrations.RunPython.noop,
        ),
    ]