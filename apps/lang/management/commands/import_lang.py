from csv import DictReader
from django.core.management.base import BaseCommand
from django.db import transaction

from lang.models import String, Link, LinkCollection


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--code', dest='lang_code')
        parser.add_argument('filename')

    def handle(self, *args, **kwargs):
        filename = kwargs['filename']
        lang_code = kwargs['lang_code']
        self.import_language(filename, lang_code)

    @transaction.atomic
    def import_language(self, filename, lang_code):
        reader = DictReader(open(filename))
        for i, row in enumerate(reader):
            print(f'Loading row #{i}')
            string_value = row['sp_text_new']
            string, _ = String.objects.get_or_create(
                language=lang_code,
                value=string_value,
            )

            links = row['links'].split(', ')
            for link_id in links:
                if len(link_id.strip()) == 0:
                    continue
                collection_key, link_key = link_id.split(': ')
                collection, _ = LinkCollection.objects.get_or_create(
                    key=collection_key
                )

                link, _ = Link.objects.get_or_create(
                    link_collection=collection,
                    key=link_key,
                    string=string,
                    language=lang_code
                )
