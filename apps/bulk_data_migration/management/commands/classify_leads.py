from django.core.management.base import BaseCommand

from lead.models import Lead
from lead.tasks import send_lead_text_to_deepl


class Command(BaseCommand):
    help = 'Classify leads whose preview have been generated but do not have classified_doc_id'

    def handle(self, *args, **options):
        lead_ids = Lead.objects.filter(
            leadpreview__isnull=False,
            leadpreview__classified_doc_id__isnull=True,
        ).values_list('id', flat=True)

        for lead_id in lead_ids:
            send_lead_text_to_deepl.delay(lead_id)
