import logging
from django.core.management.base import BaseCommand
from lead.tasks import extract_thumbnail
from lead.models import Lead
from django.db.models import Q


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generates and saves thumbnail for lead'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lead_id',
            nargs='+',
            type=int,
            help='List of id of leads'
        )

        parser.add_argument(
            '--existing',
            action='store_true',
            help='For existing leads without thumbnails',
        )

    def handle(self, *args, **options):
        if options['lead_id']:
            for lead_id in options['lead_id']:
                logger.warning('Generating thumbnail for {}'.format(lead_id))
                extract_thumbnail(lead_id)
        elif options['existing']:
            leads = Lead.objects.filter(
                Q(leadpreview__thumbnail__isnull=True) |
                Q(leadpreview__thumbnail='')
            ).distinct()
            for lead in leads:
                logger.warning('Generating thumbnail for {}'.format(lead.id))
                extract_thumbnail(lead.id)
