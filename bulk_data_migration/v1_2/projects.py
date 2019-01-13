from django.db import transaction
from project.models import Project


def migrate_projects(*args, **kwargs):
    filter_args = kwargs
    with transaction.atomic():
        for project in Project.objects.filter(**filter_args):
            project.update_status()
