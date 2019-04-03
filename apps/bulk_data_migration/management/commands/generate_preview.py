from django.core.management.base import BaseCommand

from lead.tasks import generate_previews


class Command(BaseCommand):
    help = 'Extract preview/images from leads'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lead_id',
            nargs='+',
            type=int,
            help='List of lead ids'
        )

    def handle(self, *args, **options):
        if options['lead_id']:
            generate_previews.delay(options['lead_id'])
        else:
            generate_previews.delay()
