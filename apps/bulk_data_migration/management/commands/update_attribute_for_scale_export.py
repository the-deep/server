from django.core.management.base import BaseCommand

from entry.models import Attribute
from entry.utils import update_entry_attribute


class Command(BaseCommand):
    help = 'Update attributes to export scales'

    def handle(self, *args, **options):
        for each in Attribute.objects.filter(widget__widget_id__in=['scaleWidget', 'conditionalWidget']):
            update_entry_attribute(each)
