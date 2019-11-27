import signal
import logging
from django.core.management.base import BaseCommand
from lead.tasks import extract_thumbnail
from lead.models import Lead
from django.db.models import Q


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


class timeout:
    def __init__(self, seconds):
        self._seconds = seconds

    def __enter__(self):
        # Register and schedule the signal with the specified time
        signal.signal(signal.SIGALRM, timeout._raise_timeout)
        signal.alarm(self._seconds)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Unregister the signal so it won't be triggered if there is
        # no timeout
        signal.signal(signal.SIGALRM, signal.SIG_IGN)

    @staticmethod
    def _raise_timeout(signum, frame):
        raise TimeoutError


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
            count = leads.count()
            index = 1
            for lead in leads.iterator(chunk_size=500):
                try:
                    print(f'({index}/{count}) Generating thumbnail for {lead.id}')
                    with timeout(seconds=60):
                        extract_thumbnail(lead.id)
                except TimeoutError:
                    logger.error('Thumbnail Extraction Timeout!!', exc_info=True)
                except Exception:
                    logger.error('Thumbnail Extraction Failed!!', exc_info=True)
                index += 1
