from django.core.management.base import BaseCommand
from django.db.models.functions import StrIndex
from django.db.models import F

import math

from lead.models import Lead
from entry.models import Entry



class Command(BaseCommand):
    help = 'Check if entry text is in lead text and populate dropped_text accordingly.'

    def handle(self, *args, **options):
        chunk_size = 200
        leads = Lead.objects.filter(
            leadpreview__text_extract__isnull=False
        )
        leads_count = leads.count()
        total_chunks = math.ceil(leads_count/chunk_size)
        n = 1
        for lead in leads.iterator(chunk_size=chunk_size):
            print(f'Updating entries from lead chunk {n} of {total_chunks}')
            lead.entry_set.filter(entry_type=Entry.EXCERPT).annotate(
                index=StrIndex('lead__leadpreview__text_extract', F('excerpt'))
            ).filter(index__gt=0).update(
                dropped_excerpt=F('excerpt')
            )
            n += 1
        print('Done.')
