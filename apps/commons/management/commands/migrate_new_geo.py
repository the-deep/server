from itertools import chain

from django.core import serializers
from django.contrib.admin.utils import NestedObjects
from django.core.management.base import BaseCommand

from geo.models import Region


class Command(BaseCommand):
    help = 'Dump the geo areas'

    def handle(self, *args, **kwargs):
        # replace the project id with the project_id that you are exporting
        queryset = Region.objects.filter(project=2)
        collector = NestedObjects(using='default')
        collector.collect(list(queryset))

        objects = list(chain.from_iterable(collector.data.values()))
        with open("export_geo_locations", "w") as f:
            f.write(serializers.serialize("json", objects))
