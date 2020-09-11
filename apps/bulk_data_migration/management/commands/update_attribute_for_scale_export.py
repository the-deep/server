from django.core.management.base import BaseCommand

from entry.models import Attribute


class Command(BaseCommand):
    help = 'Update attributes to export scales'

    def handle(self, *args, **options):
        for each in Attribute.objects.all():
            each.save()
