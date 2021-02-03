import botocore
from django.db.models.functions import Cast
from django.contrib.postgres.fields.jsonb import KeyTransform, KeyTextTransform
from django.core.management.base import BaseCommand
from django.db.models import Q, IntegerField

from gallery.models import File


class Command(BaseCommand):
    def handle(self, *args, **options):
        qs = File.objects.annotate(
            file_size=Cast(
                KeyTextTransform('file_size', 'metadata'),
                IntegerField(),
            )
        ).filter(~Q(file=''), file_size__isnull=True)
        to_process_count = qs.count()
        index = 1

        for file in qs.iterator():
            file.metadata = file.metadata or {}
            try:
                file.metadata['file_size'] = file.file.size
                print(f'Processed {index}/{to_process_count}', end='\r', flush=True)
                file.save(update_fields=['metadata'])
                index += 1
            except botocore.exceptions.ClientError:
                pass
        print(f'\nProcessed: {index}/{to_process_count} files successfully')
