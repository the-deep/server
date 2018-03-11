from django.core.management.base import BaseCommand
from profiling.profiler import Profiler

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
        autofixture.create('project.Project', 5, field_values={
            'created_by': user,
        })

        print('creating leads')
        autofixture.create('lead.Lead', 1000, field_values={
            'created_by': user,
        })

        p.profile_get(
            '/api/v1/leads/?'
            'status=pending&'
            'assignee={0}&'
            'published_on__lt=5000-01-10'
            'assignee={0}&'
            'search=abc&'
            ''.format(
                ','.join([str(users[1].id), str(users[2].id)]),
            ))
