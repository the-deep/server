from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.functions import Length

from lead.models import Lead
from lead.tasks import classify_lead


class Command(BaseCommand):
    help = 'Classify leads whose preview have been generated but do not have classified_doc_id'

    def handle(self, *args, **options):
        leads = Lead.objects.filter(
            ~Q(leadpreview=None),
            ~Q(leadpreview__text_extract=None),
            ~Q(leadpreview__text_extract__regex=r'^\W*$'),
            leadpreview__classified_doc_id=None,
        ).annotate(
            text_len=Length('leadpreview__text_extract')
        ).filter(
            text_len__lte=5000  # Texts of length 5000 do not pose huge computation in DEEPL
        ).prefetch_related('leadpreview')[:50]

        print('\nNOTE: that only 50 leads will be classified at a time.\n')

        for i, lead in enumerate(leads):
            print('Classifying lead', lead.id, 'Lead Count:', i + 1)
            classify_lead(lead)
            print('Complete!!\n')
