from django.core.management.base import BaseCommand
from profiling.profiler import Profiler
from lead.autofixtures import create_many_leads
from project.models import Project

import autofixture


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        p = Profiler()

        print('creating users')
        users = autofixture.create('auth.User', 20, overwrite_defaults=True)
        user = users[0]
        p.authorise_with(user)

        print('creating regions')
        autofixture.create('geo.Region', 5, field_values={
            'created_by': user,
        })

        print('creating projects')
        Project.objects.all().delete()
        autofixture.create_one('project.Project', field_values={
            'created_by': user,
        })
        project = Project.objects.first()

        print('creating leads')
        create_many_leads(10000, user, project)
        # autofixture.create('lead.Lead', 1000, field_values={
        #     'created_by': user,
        # })

        p.profile_get(
            '/api/v1/leads/?'
            'status=pending&'
            'published_on__lt=5000-01-10'
            'assignee={0}&'
            'search=lorem&'
            ''.format(
                ','.join([str(users[1].id), str(users[2].id)]),
            ))
