from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.apps import apps


IGNORE_MODELS = [
    f'ary.{model}'
    for model in ['Assessment']
]


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
