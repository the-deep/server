from itertools import chain

from django.core import serializers
from django.contrib.admin.utils import NestedObjects
from django.core.management.base import BaseCommand

from project.models import Project


class Command(BaseCommand):
    help = 'Dump the project and all associated with it'

    def handle(self, *args, **kwargs):
        collector = NestedObjects(using="default")
        # replace the project id with the project_id that you are exporting
        collector.collect([Project.objects.get(id=2)])

        objects = list(chain.from_iterable(collector.data.values()))
        with open("export_project.json", "w") as f:
            f.write(serializers.serialize("json", objects))
