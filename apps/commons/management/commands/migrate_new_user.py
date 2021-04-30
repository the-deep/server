from itertools import chain

from django.core import serializers
from django.contrib.admin.utils import NestedObjects
from django.core.management.base import BaseCommand

from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Dump User and all associated with it'

    def handle(self, *args, **kwargs):
        # replace the project id with the project_id that you are exporting
        queryset = User.objects.filter(project=2)
        collector = NestedObjects(using="default")
        collector.collect(list(queryset))

        objects = list(chain.from_iterable(collector.data.values()))
        with open("backup_user.json", "w") as f:
            f.write(serializers.serialize("json", objects))
