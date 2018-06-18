from django.core.management.base import BaseCommand
from profiling.profiler import Profiler
from project.models import Project, ProjectMembership

import autofixture


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        p = Profiler()

        print('Creating users')
        users = autofixture.create('auth.User', 20, overwrite_defaults=True)
        user = users[0]
        p.authorise_with(user)

        print('Creating regions')
        autofixture.create('geo.Region', 5, field_values={
            'created_by': user,
        })

        print('Creating projects')
        Project.objects.all().delete()
        autofixture.create_one('project.Project', field_values={
            'created_by': user,
        })
        project = Project.objects.first()
        if not ProjectMembership.objects.filter(project=project, member=user)\
                .exists():
            ProjectMembership.objects.create(project=project, member=user,
                                             role='admin')

        print('Creating leads')
        # create_many_leads(1000, user, project)
        autofixture.create('lead.Lead', 1000, field_values={
            'created_by': user,
        })

        print('Starting profiling')
        p.profile_get(
            '/api/v1/leads/?'
            'status=pending&'
            'published_on__lt=2016-01-10&'
            'assignee={0}&'
            'search=lorem&'
            'limit=100&'
            ''.format(users[2].id)
        )

        p.__del__()
