from django.core.management.base import BaseCommand

from entry.models import Attribute
from entry.utils import update_entry_attribute


class Command(BaseCommand):
    help = 'Update attributes to export widget'

    def add_arguments(self, parser):
        parser.add_argument(
            '--widget'
        )

    def handle(self, *args, **options):
        widget_name = options['widget']
        for attr in Attribute.objects.filter(widget__widget_id=widget_name):
            update_entry_attribute(attr)
        for attr in Attribute.objects.filter(widget__widget_id='conditionalWidget'):
            if widget_name in [each['widget']['widget_id'] for each in attr.widget.properties['data']['widgets']]:
                update_entry_attribute(attr)
