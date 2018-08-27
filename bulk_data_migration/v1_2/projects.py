from django.db import transaction
from project.models import Project


def migrate_projects():
    with transaction.atomic():
        for project in Project.objects.all():
            project.update_status()
