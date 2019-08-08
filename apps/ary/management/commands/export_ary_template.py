from django.core.management import call_command
from django.core.serializers import serialize
from django.core.management.base import BaseCommand
from django.apps import apps
from fixture_magic.utils import (
    add_to_serialize_list, serialize_me, serialize_fully, seen,
)


IGNORE_MODELS = [
    f'ary.{model}'
    for model in ['Assessment']
]


def export_ary_fixture():
    for model in apps.get_app_config('ary').get_models():
        label = model._meta.label
        if label in IGNORE_MODELS:
            continue
        objs = model.objects.all()
        add_to_serialize_list(objs)
    serialize_fully()
    data = serialize(
        'json',
        sorted(
            [o for o in serialize_me if o is not None],
            key=lambda x: (f'{x._meta.app_label}.{x._meta.model_name}', x.pk),
        ),
        indent=2,
        use_natural_foreign_keys=False,
        use_natural_primary_keys=False
    )
    del serialize_me[:]
    seen.clear()
    return data


class Command(BaseCommand):

    def handle(self, *args, **options):
        export_files = []
        for model in apps.get_app_config('ary').get_models():
            label = model._meta.label
            if label in IGNORE_MODELS:
                continue
            filename = f'/tmp/{label}.json'
            export_files.append(filename)
            with open(filename, 'w+') as f:
                call_command('dump_object', label, '*', stdout=f)
        call_command('merge_fixtures', *export_files)
