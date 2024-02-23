from django.core.management.base import BaseCommand

from project.models import Project

from project.tasks import generate_viz_stats


class Command(BaseCommand):
    help = 'Generate the Project Viz Stats'

    def handle(self, *arg, **options):
        generate_project_viz_stats()


def generate_project_viz_stats():
    project_qs = Project.objects.filter(
        is_visualization_enabled=True
    )
    for project in project_qs:
        generate_viz_stats(project.id, force=True)
